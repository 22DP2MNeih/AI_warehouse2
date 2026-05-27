import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Concatenate, Multiply
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Max, Min
from .models import Order, Company, Warehouse, Product, CompanyProduct, WarehouseStock

COUNTRY_CODES = ['LV', 'LT', 'EE', 'DE', 'PL', 'FI', 'SE', 'GB', 'US', 'FR', 'IT', 'ES', 'NL', 'OT']
COUNTRY_TO_INDEX = {code: idx for idx, code in enumerate(COUNTRY_CODES)}

class GlobalInventoryModel:
    """
    Kontekstuālais detaļu pieprasījuma un savienojumu mākslīgais neironu tīkls.
    Izmanto koplietojamu globālo bāzi (Backbone) universālai loģikai un specifisku filtrēšanas 
    ceļu (Gating Pathway), kas balstīts uz noliktavas krājumu specifiku un lokāciju, 
    lai pielāgotu pieprasījuma prognozes.
    """
    def __init__(self, sequence_length=14, n_features=1, service_level=0.95):
        self.sequence_length = sequence_length
        self.n_features = n_features
        # Ierobežo servisa līmeni no 90% līdz 99.9%, lai novērstu ekstrēmas prognozes
        self.service_level = max(0.90, min(service_level, 0.999))
        self.model_path = "global_inventory_model.weights.h5"
        self.metadata_path = "global_inventory_model.metadata.json"
        
        # Ielādē vai iestata noklusēto apmācīto periodu (horizontu)
        self.trained_horizon = 30
        self._load_metadata()
        
        # Dinamiski nosaka detaļas pazīmju dimensiju
        self.part_feature_dim = 16 
        
        # Maksimālais produkta ID noliktavas izmantojuma vektora lielumam
        max_id = Product.objects.aggregate(Max('id'))['id__max']
        self.max_part_id = (max_id or 0) + 1000 # Pievieno rezervi jaunām detaļām
        
        self.model = self._build_model()
        self._load_weights_if_exist()

    def _load_metadata(self):
        # Ielādē modeļa metadatus, ja tādi eksistē
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    meta = json.load(f)
                    self.trained_horizon = meta.get("trained_horizon", 30)
            except Exception as e:
                print(f"Neizdevās ielādēt globālā modeļa metadatus: {e}")

    def _save_metadata(self, horizon):
        # Saglabā apmācības horizontu turpmākai mērogošanai
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump({"trained_horizon": horizon}, f)
            self.trained_horizon = horizon
        except Exception as e:
            print(f"Neizdevās saglabāt globālā modeļa metadatus: {e}")

    def pinball_loss(self, y_true, y_pred):
        """
        Pielāgota zaudējumu funkcija (Pinball Loss), kas nepieciešama kvantiļu regresijai.
        Soda modeli vairāk par iztrūkumu nekā par pārpalikumu, balstoties uz servisa līmeni.
        """
        q = tf.constant(self.service_level, dtype=tf.float32)
        error = y_true - y_pred
        return tf.reduce_mean(tf.maximum(q * error, (q - 1) * error))

    def _build_model(self):
        """
        Definē Funkcionālā API arhitektūru (Shared Global Backbone + Gating Pathway).
        """
        # Ievades slāņi
        recent_history_input = Input(shape=(self.sequence_length, self.n_features), name="recent_history")
        part_features_input = Input(shape=(self.part_feature_dim,), name="part_features")
        warehouse_usage_input = Input(shape=(self.max_part_id,), name="warehouse_usage")
        warehouse_country_input = Input(shape=(1,), name="warehouse_country", dtype="int32")

        # Globālās loģikas ceļš (Global Brain)
        history_lstm = LSTM(32, return_sequences=False)(recent_history_input)
        history_drop = Dropout(0.2)(history_lstm)
        global_concat = Concatenate()([history_drop, part_features_input])
        global_dense1 = Dense(64, activation='relu')(global_concat)
        global_drop = Dropout(0.2)(global_dense1)
        global_logic = Dense(32, activation='relu', name="global_logic")(global_drop)

        # Noliktavas specifikas filtrs (Gating Pathway)
        usage_reduced = Dense(64, activation='relu')(warehouse_usage_input)
        usage_drop = Dropout(0.2)(usage_reduced)
        
        # Valsts iegulšana (Embedding)
        from tensorflow.keras.layers import Embedding, Flatten
        country_embedding = Embedding(input_dim=len(COUNTRY_CODES), output_dim=8, name="country_embedding")(warehouse_country_input)
        country_flat = Flatten()(country_embedding)

        warehouse_concat = Concatenate()([usage_drop, country_flat])
        warehouse_dense = Dense(32, activation='relu')(warehouse_concat)
        # Sigmoid funkcija pārvērš vērtības diapazonā [0, 1] - darbojas kā "slēdži"
        warehouse_fingerprint = Dense(32, activation='sigmoid', name="warehouse_fingerprint")(warehouse_dense)

        # Mijiedarbības slānis (Hadamarda reizinājums)
        # Sareizina globālo loģiku ar noliktavas filtru elementu pa elementam
        interaction = Multiply(name="hadamard_product")([global_logic, warehouse_fingerprint])

        # Gala slāņi prognozes iegūšanai
        out_dense = Dense(16, activation='relu')(interaction)
        output = Dense(1, name="prediction")(out_dense)

        model = Model(
            inputs=[recent_history_input, part_features_input, warehouse_usage_input, warehouse_country_input], 
            outputs=output
        )
        
        optimizer = Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss=self.pinball_loss, metrics=['mae'])
        return model

    def _load_weights_if_exist(self):
        # Ielādē modeļa svarus, lai turpinātu apmācību vai veiktu prognozes
        if os.path.exists(self.model_path):
            try:
                self.model.load_weights(self.model_path)
            except Exception as e:
                print(f"Neizdevās ielādēt globālā modeļa svarus: {e}")

    def get_callbacks(self):
        # Pārtrauc apmācību agrāk, ja zudums nesamazinās, un saglabā labākos svarus
        return [
            EarlyStopping(monitor='loss', patience=5, restore_best_weights=True, verbose=1),
            ModelCheckpoint(filepath=self.model_path, monitor='loss', save_best_only=True, save_weights_only=True, verbose=0)
        ]

    def _extract_part_features(self, product):
        """
        Izgūst detaļas pazīmes un piesaista tās fiksēta izmēra vektoram.
        Pašlaik izmanto kategoriju. Nākotnē pielāgojams svaram/materiālam.
        """
        features = np.zeros(self.part_feature_dim, dtype=np.float32)
        # Heshē kategorijas tekstu uz dažiem indeksiem, lai simulētu iegulšanu (embedding)
        category = product.category or "UNKNOWN"
        hash_val = hash(category)
        features[hash_val % self.part_feature_dim] = 1.0
        
        # Piemērs nākotnes pazīmēm, ko pievienot datubāzei:
        # features[10] = product.weight if hasattr(product, 'weight') else 0.0
        # features[11] = hash(product.material) % 5 if hasattr(product, 'material') else 0.0
        return features

    def _get_warehouse_usage_vector(self, warehouse):
        """
        Generē normalizētu patēriņa vektoru konkrētajai noliktavai.
        """
        usage_vector = np.zeros(self.max_part_id, dtype=np.float32)
        
        # Iegūst vēsturisko patēriņu šai noliktavai
        orders = Order.objects.filter(
            from_warehouse=warehouse,
            order_type='CONSUME',
            status='COMPLETED'
        ).values('product_listing__product__id').annotate(total=Sum('quantity'))
        
        total_throughput = 0
        for item in orders:
            pid = item['product_listing__product__id']
            qty = item['total']
            if pid and pid < self.max_part_id:
                usage_vector[pid] = qty
                total_throughput += qty
                
        # Normalizē vektoru, lai iegūtu relatīvo sadalījumu
        if total_throughput > 0:
            usage_vector = usage_vector / total_throughput
            
        return usage_vector

    def _get_warehouse_country_index(self, warehouse):
        """
        Atgriež standarta veselu skaitli, kas atbilst noliktavas valsts kodam.
        """
        country_code = warehouse.country_code or 'LV'
        country_code = country_code.upper()
        return COUNTRY_TO_INDEX.get(country_code, COUNTRY_TO_INDEX['OT'])

    def fetch_and_preprocess(self, prediction_period=30):
        """
        Izgūst VISUS anonimizētos datus globāli, lai apmācītu kopējo modeli.
        """
        orders = Order.objects.filter(
            order_type='CONSUME',
            status='COMPLETED',
            from_warehouse__isnull=False
        ).select_related('product_listing__product', 'from_warehouse').order_by('created_at')

        if not orders.exists():
            return None, None

        # Nosaka sākuma/beigu datumu globāli, lai izveidotu ikdienas laika skalu
        agg = orders.aggregate(min_date=Min('created_at'), max_date=Max('created_at'))
        start_date = agg['min_date'].date()
        end_date = agg['max_date'].date()
        db_span = (end_date - start_date).days + 1

        # Dinamiski nosaka apmācības horizontu, lai tas ideāli ietilptu datubāzes laika diapazonā
        self.train_horizon = min(prediction_period, max(3, db_span - self.sequence_length - 2))
        self._save_metadata(self.train_horizon)

        # Grupē datus pēc Noliktava -> Produkts -> Datums
        data_by_w_p = {}
        warehouse_cache = {}
        product_cache = {}
        
        for o in orders:
            wid = o.from_warehouse.id
            pid = o.product_listing.product.id
            day = o.created_at.date()
            
            if wid not in warehouse_cache:
                warehouse_cache[wid] = o.from_warehouse
            if pid not in product_cache:
                product_cache[pid] = o.product_listing.product
                
            if wid not in data_by_w_p:
                data_by_w_p[wid] = {}
            if pid not in data_by_w_p[wid]:
                data_by_w_p[wid][pid] = {}
            if day not in data_by_w_p[wid][pid]:
                data_by_w_p[wid][pid][day] = 0
            data_by_w_p[wid][pid][day] += o.quantity

        X_recent = []
        X_part = []
        X_w_usage = []
        X_w_country = []
        y = []
        
        # Iepriekš aprēķina vektorus, lai ieekonomētu laiku
        w_usage_cache = {}
        w_country_cache = {}
        for wid, warehouse in warehouse_cache.items():
            w_usage_cache[wid] = self._get_warehouse_usage_vector(warehouse)
            w_country_cache[wid] = self._get_warehouse_country_index(warehouse)

        p_feature_cache = {}
        for pid, product in product_cache.items():
            p_feature_cache[pid] = self._extract_part_features(product)

        for wid, w_data in data_by_w_p.items():
            for pid, daily_data in w_data.items():
                w_usage = w_usage_cache[wid]
                w_country = w_country_cache[wid]
                p_feat = p_feature_cache[pid]

                # Ģenerē pilnu laika rindu no start_date līdz end_date globāli
                full_series = []
                for d in range(db_span):
                    current = start_date + timedelta(days=d)
                    full_series.append(daily_data.get(current, 0))

                seq_len = self.sequence_length
                horizon = self.train_horizon

                # Veido slīdošos logus (sliding windows) laika rindu apmācībai
                for i in range(len(full_series) - seq_len - horizon + 1):
                    window_x = full_series[i : i + seq_len]
                    window_y = sum(full_series[i + seq_len : i + seq_len + horizon])
                    
                    X_recent.append([[val] for val in window_x])
                    X_part.append(p_feat)
                    X_w_usage.append(w_usage)
                    X_w_country.append([w_country])
                    y.append(window_y)

        if not X_recent:
            return None, None

        return (
            [
                np.array(X_recent, dtype=np.float32), 
                np.array(X_part, dtype=np.float32),
                np.array(X_w_usage, dtype=np.float32),
                np.array(X_w_country, dtype=np.int32)
            ],
            np.array(y, dtype=np.float32)
        )

    def train_model(self, epochs=50, prediction_period=30):
        """
        Apmāca koplietojamo globālo neironu tīklu.
        """
        X, y = self.fetch_and_preprocess(prediction_period=prediction_period)
        if X is None or len(y) < 5:
            return False, "Nav pietiekami daudz vēsturisko datu, lai veiktu apmācību."

        val_split = 0.2 if len(y) > 20 else 0.0

        history = self.model.fit(
            X, y,
            validation_split=val_split,
            epochs=epochs,
            batch_size=min(32, len(y)),
            callbacks=self.get_callbacks(),
            verbose=1
        )
        return True, "Apmācība veiksmīgi pabeigta."

    def predict_for_part(self, product_listing, warehouse, max_history_days=30):
        """
        Veic prognozi konkrētai precei, izmantojot globālo modeli un lokālo realitāti.
        """
        end_date = timezone.now().date()
        start_date = timezone.now().date() - timedelta(days=self.sequence_length)
        
        # Izgūst nesenākos pasūtījumus
        orders = Order.objects.filter(
            product_listing=product_listing,
            from_warehouse=warehouse,
            order_type='CONSUME',
            status='COMPLETED',
            created_at__date__gte=start_date
        )

        daily_data = {}
        for o in orders:
            d = o.created_at.date()
            daily_data[d] = daily_data.get(d, 0) + o.quantity

        recent_seq = []
        for d in range(self.sequence_length):
            current = start_date + timedelta(days=d)
            recent_seq.append(daily_data.get(current, 0))

        # Sagatavo ievades datus modelim
        X_recent = np.array([[ [val] for val in recent_seq ]], dtype=np.float32)
        X_part = np.array([self._extract_part_features(product_listing.product)], dtype=np.float32)
        X_w_usage = np.array([self._get_warehouse_usage_vector(warehouse)], dtype=np.float32)
        X_w_country = np.array([[self._get_warehouse_country_index(warehouse)]], dtype=np.int32)

        raw_prediction = self.model.predict([X_recent, X_part, X_w_usage, X_w_country], verbose=0)
        
        # Dinamiski mērogo prognozi no apmācītā horizonta uz pilnām 30 dienām!
        scale_factor = 30 / self.trained_horizon
        floor = max(0, int(np.ceil(raw_prediction[0][0] * scale_factor)))
        return floor


# INTEGRĀCIJAS UN FONDA FUNKCIJAS
def predict_floor_for_stock(stock_item, company, historical_data_mock=None):
    """
    Savienojošā funkcija starp Django datu bāzi un AI modeli.
    """
    service_level = float(company.service_level) if company.service_level is not None else 0.95
    engine = GlobalInventoryModel(sequence_length=7, service_level=service_level)
    
    # Ja modelis nav apmācīts, atgriež noklusētos drošības krājumus vai moka datus
    if not os.path.exists(engine.model_path):
        if historical_data_mock is None or historical_data_mock == 0:
            return 5 # Drošais minimums
        else:
            return int(historical_data_mock * service_level)
            
    try:
        prediction = engine.predict_for_part(stock_item.company_product, warehouse=stock_item.warehouse) 
        stock_item.ai_stock_floor = prediction
        stock_item.last_ai_update = timezone.now()
        stock_item.save()
        return prediction
    except Exception as e:
        print("Prognozes kļūda:", e)
        return 10

def refresh_all_predictions():
    """
    Globāls fonā palaižams uzdevums, kas atjaunina AI prognozētos krājumu sliekšņus visām precēm.
    Paredzēts palaišanai reizi dienā (piemēram, ar Celery vai Cron).
    """
    from .models import WarehouseStock
    
    engine = GlobalInventoryModel(sequence_length=7)
    
    if not os.path.exists(engine.model_path):
        return

    stocks = WarehouseStock.objects.all().select_related('company_product__product', 'warehouse')
    for s in stocks:
        try:
            floor = engine.predict_for_part(s.company_product, warehouse=s.warehouse)
            s.ai_stock_floor = floor
            s.last_ai_update = timezone.now()
            s.save()
        except Exception as e:
            print(f"Kļūda atjauninot prognozi krājumam {s.id}: {e}")
            continue