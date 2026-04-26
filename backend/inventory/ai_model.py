import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Order, Company

# GALVENĀ PROGNOZĒŠANAS KLASE
# Galvenā klase krājumu prognozēšanai izmantojot mākslīgo intelektu.
# Šī klase parūpējas par TensorFlow modeļa izveidi, datu apstrādi un krājumu sliekšņu aprēķināšanu.
class InventoryForecastModel:
    """
    Klase, kas atbild par LSTM neironu tīkla izveidi, apmācību un 
    krājumu patēriņa prognozēšanu konkrētam uzņēmumam.
    """
    def __init__(self, company_id, sequence_length=14, n_features=1, service_level=0.95):
        # Inicializē modeļa parametrus: uzņēmuma ID, vēstures loga garumu un servisa līmeni
        self.company_id = company_id
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.service_level = max(0.90, min(service_level, 0.999))
        
        # Ceļš uz failu, kurā tiek glabāti modeļa svari
        self.model_path = f"best_inventory_model_company_{self.company_id}.weights.h5"
        
        # Izveido modeļa struktūru un mēģina ielādēt eksistējošos svarus
        self.model = self._build_model()
        self._load_weights_if_exist()

    def pinball_loss(self, y_true, y_pred):
        """
        Pielāgota zaudējumu funkcija (Pinball Loss), kas nepieciešama kvantiļu regresijai.
        Tā palīdz modelim prognozēt vērtību ar noteiktu "drošības rezervi" (service level),
        nevis vienkārši vidējo patēriņu.
        """
        q = tf.constant(self.service_level, dtype=tf.float32)
        error = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * error, (q - 1) * error))

    # Modeļa arhitektūras definēšana.
    # Tiek izmantots LSTM (Long Short-Term Memory) tīkls, kas ir piemērots laika rindu datiem.
    # Modelis sastāv no diviem LSTM slāņiem un blīvajiem (Dense) slāņiem gala rezultāta aprēķināšanai.
    def _build_model(self):
        """
        Definē LSTM neironu tīkla arhitektūru laika rindu analīzei.
        """
        model = Sequential([
            # Pirmais LSTM slānis ar 64 neironiem, kas atgriež secību nākamajam slānim
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length, self.n_features)),
            Dropout(0.2), # Datu atmetināšana, lai novērstu pārmācīšanos
            
            # Otrais LSTM slānis, kas apkopo informāciju
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            
            # Pilnībā savienotie slāņi rezultāta iegūšanai
            Dense(16, activation='relu'),
            Dense(1) # Izvade: prognozētais preču daudzums
        ])
        
        optimizer = Adam(learning_rate=0.001)
        
        # Modelis tiek kompilēts, izmantojot pielāgoto Pinball zaudējumu funkciju
        model.compile(optimizer=optimizer, loss=self.pinball_loss, metrics=['mae'])
        return model

    def _load_weights_if_exist(self):
        """
        Pārbauda, vai diskā eksistē iepriekš apmācīti modeļa svari, un ielādē tos.
        """
        if os.path.exists(self.model_path):
            try:
                self.model.load_weights(self.model_path)
            except Exception as e:
                print(f"Could not load weights for company {self.company_id}: {e}")

    def get_callbacks(self):
        """
        Definē atpakaļsaukšanas funkcijas apmācības procesam:
        - EarlyStopping: pārtrauc apmācību, ja rezultāti vairs neuzlabojas.
        - ModelCheckpoint: automātiski saglabā labāko modeļa versiju.
        """
        return [
            EarlyStopping(monitor='loss', patience=5, restore_best_weights=True, verbose=1),
            ModelCheckpoint(filepath=self.model_path, monitor='loss', save_best_only=True, save_weights_only=True, verbose=0)
        ]

    # Datu iegūšana no datubāzes un to sagatavošana modeļa apmācībai.
    # Šeit mēs apkopojam vēsturiskos patēriņa datus (CONSUME pasūtījumus), sakārtojam tos pa dienām
    # un izveidojam slīdošā loga (sliding window) sekvences, ko modelis var saprast.
    def fetch_and_preprocess(self, prediction_period=30):
        """
        Iegūst datus no datubāzes un sagatavo tos neironu tīklam (X un y masīvi).
        """
        # Atlasa pabeigtos patēriņa pasūtījumus konkrētajam uzņēmumam
        orders = Order.objects.filter(
            product_listing__company_id=self.company_id,
            order_type='CONSUME',
            status='COMPLETED'
        ).order_by('created_at')

        if not orders.exists():
            return None, None

        # Grupē datus pēc preces un datuma
        data_by_part = {}
        for o in orders:
            pid = o.product_listing.id
            day = o.created_at.date()
            if pid not in data_by_part:
                data_by_part[pid] = {}
            if day not in data_by_part[pid]:
                data_by_part[pid][day] = 0
            data_by_part[pid][day] += o.quantity

        X, y = [], []
        # Izveido slīdošā loga secības katrai precei
        for pid, daily_data in data_by_part.items():
            sorted_days = sorted(daily_data.keys())
            if not sorted_days:
                continue
            
            start_date = sorted_days[0]
            end_date = sorted_days[-1]
            total_days = (end_date - start_date).days + 1
            
            # Aizpilda izlaistās dienas ar nulles patēriņu
            full_series = []
            for d in range(total_days):
                current = start_date + timedelta(days=d)
                full_series.append(daily_data.get(current, 0))

            seq_len = self.sequence_length
            horizon = prediction_period

            # Izveido X (ievades vēsture) un Y (nākotnes perioda kopējais patēriņš)
            for i in range(len(full_series) - seq_len - horizon + 1):
                window_x = full_series[i : i + seq_len]
                window_y = sum(full_series[i + seq_len : i + seq_len + horizon])
                X.append([[val] for val in window_x]) # Pārveido formātā (secība, pazīme)
                y.append(window_y)

        if not X:
            return None, None

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    # Modeļa apmācības process.
    # Ja datu ir pietiekami, modelis tiek apmācīts, lai atpazītu likumsakarības vēsturiskajā patēriņā
    # un spētu prognozēt nepieciešamo krājumu daudzumu nākotnei.
    def train_model(self, epochs=50, prediction_period=30):
        """
        Veic modeļa apmācību ar uzņēmuma vēsturiskajiem datiem.
        """
        X, y = self.fetch_and_preprocess(prediction_period=prediction_period)
        if X is None or len(X) < 5:
            return False, "Not enough historical consumption data to train."

        # Ja datu apjoms atļauj, izmanto 20% datu validācijai
        val_split = 0.2 if len(X) > 20 else 0.0

        history = self.model.fit(
            X, y,
            validation_split=val_split,
            epochs=epochs,
            batch_size=min(32, len(X)),
            callbacks=self.get_callbacks(),
            verbose=1
        )
        return True, "Training completed successfully."

    # Konkrētas detaļas patēriņa prognozēšana.
    # Izmantojot pēdējo dienu datus, modelis aprēķina "drošos krājumus" (floor), 
    # kas nepieciešami, lai izvairītos no deficīta.
    def predict_for_part(self, product_listing_id, warehouse_id=None, max_history_days=30):
        """
        Veic prognozi konkrētai precei, izmantojot pēdējo dienu vēsturi.
        """
        end_date = timezone.now().date()
        # start_date = end_date - timedelta(days=self.sequence_length - 1)
        start_date = timezone.now().date() - 1
        
        filter_kwargs = {
            'product_listing_id': product_listing_id,
            'order_type': 'CONSUME',
            'status': 'COMPLETED',
            'created_at__date__gte': start_date
        }
        if warehouse_id:
            filter_kwargs['from_warehouse_id'] = warehouse_id

        orders = Order.objects.filter(**filter_kwargs)

        # Sagatavo pēdējo dienu patēriņa masīvu
        daily_data = {}
        for o in orders:
            d = o.created_at.date()
            daily_data[d] = daily_data.get(d, 0) + o.quantity

        recent_seq = []
        for d in range(self.sequence_length):
            current = start_date + timedelta(days=d)
            recent_seq.append(daily_data.get(current, 0))

        # Pārveido datus neironu tīkla ievades formātā
        X_input = np.array([[ [val] for val in recent_seq ]], dtype=np.float32)
        raw_prediction = self.model.predict(X_input, verbose=0)
        
        # Noapaļo rezultātu uz augšu un nodrošina, ka tas nav negatīvs
        floor = max(0, int(np.ceil(raw_prediction[0][0])))
        return floor

# INTEGRĀCIJAS UN FONDA FUNKCIJAS
def predict_floor_for_stock(stock_item, company, historical_data_mock=None):
    """
    Savienojošā funkcija starp Django datu bāzi un AI modeli.
    Izmanto modeli, lai noteiktu 'drošības līmeņa' krājumu slieksni.
    """
    service_level = float(company.service_level) if company.service_level is not None else 0.95
    
    engine = InventoryForecastModel(company_id=company.id, sequence_length=14, service_level=service_level)
    
    # Ja modelis vēl nav apmācīts, izmanto vienkāršotu heiristiku vai noklusējuma vērtību
    if not os.path.exists(engine.model_path):
        if historical_data_mock is None or historical_data_mock == 0:
            return 5 # Drošais minimums
        else:
            return int(historical_data_mock * service_level)
            
    # Veic prognozi, ja modelis ir gatavs
    try:
        prediction = engine.predict_for_part(stock_item.company_product.id, warehouse_id=stock_item.warehouse.id) 
        # 2. Explicitly update the database fields
        stock_item.ai_stock_floor = prediction
        stock_item.last_ai_update = timezone.now()
        stock_item.save() # This is the missing link!
        return prediction
    except Exception as e:
        print("Prediction error:", e)
        return 10

# Globāla funkcija visu uzņēmuma preču prognožu atjaunināšanai.
# Šī funkcija parasti tiek izpildīta fonā kā periodisks uzdevums, lai uzturētu datus aktuālus.
def refresh_all_predictions():
    """
    Globāls fonā palaižams uzdevums, kas atjaunina AI prognozētos krājumu sliekšņus visām precēm.
    Paredzēts palaišanai reizi dienā.
    """
    from .models import Company, WarehouseStock
    companies = Company.objects.all()
    
    for company in companies:
        service_level = float(company.service_level) if company.service_level is not None else 0.95
        engine = InventoryForecastModel(company_id=company.id, sequence_length=14, service_level=service_level)
        
        # Apstrādā tikai tos uzņēmumus, kuriem ir apmācīts modelis
        if not os.path.exists(engine.model_path):
            continue

        stocks = WarehouseStock.objects.filter(warehouse__company=company)
        for s in stocks:
            try:
                # Prognozē specifisko patēriņa modeli konkrētajai noliktavai
                floor = engine.predict_for_part(s.company_product.id, warehouse_id=s.warehouse.id)
                s.ai_stock_floor = floor
                s.last_ai_update = timezone.now()
                s.save()
            except:
                continue
