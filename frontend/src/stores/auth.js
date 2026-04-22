import { defineStore } from 'pinia';
import api from '../services/api';
import { jwtDecode } from 'jwt-decode';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        accessToken: localStorage.getItem('access_token') || null,
        refreshToken: localStorage.getItem('refresh_token') || null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        userRole: (state) => state.user?.role || '',
    },
    actions: {
        async login(credentials) {
            try {
                const response = await api.login(credentials);
                const { access, refresh } = response.data;
                this.setTokens(access, refresh);
                return true;
            } catch (error) {
                console.error("Login failed:", error);
                throw error;
            }
        },
        async register(userData) {
            try {
                await api.register(userData);
                return true;
            } catch (error) {
                console.error("Registration failed:", error);
                throw error;
            }
        },
        async logout() {
            this.accessToken = null;
            this.refreshToken = null;
            this.user = null;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            // Force reload to clear any component state or redirect
            // We'll let the component handle redirect or do it here
            // window.location.href = '/login'; 
        },
        setTokens(access, refresh) {
            this.accessToken = access;
            this.refreshToken = refresh;
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);

            this.decodeAndSetUser();
        },
        decodeAndSetUser() {
            if (this.accessToken) {
                try {
                    const decoded = jwtDecode(this.accessToken);
                    this.user = {
                        username: decoded.username,
                        role: decoded.role,
                        id: decoded.user_id,
                    };
                } catch (e) {
                    console.error("Invalid token:", e);
                    this.logout();
                }
            }
        },
        initialize() {
            this.decodeAndSetUser();
        }
    }
});
