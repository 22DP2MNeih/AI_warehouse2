import { defineStore } from 'pinia';
import api from '../services/api';
import { jwtDecode } from 'jwt-decode';

export const useAuthStore = defineStore('auth', {
    state: () => {
        const accessToken = localStorage.getItem('access_token') || null;
        const refreshToken = localStorage.getItem('refresh_token') || null;
        let user = null;

        // Synchronously extract and restore user info from token right on page load
        if (accessToken) {
            try {
                const decoded = jwtDecode(accessToken);
                // Check if the token has expired before parsing it
                const currentTime = Date.now() / 1000;
                if (decoded.exp && decoded.exp < currentTime) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                } else {
                    user = {
                        id: decoded.user_id,
                        username: decoded.username,
                        role: decoded.role,
                        company: {
                            id: decoded.company_id,
                            name: decoded.company_name
                        },
                        warehouse: {
                            id: decoded.warehouse_id,
                            name: decoded.warehouse_name
                        }
                    };
                }
            } catch (e) {
                console.error("Invalid token during boot synchronization:", e);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
            }
        }

        return {
            user,
            accessToken,
            refreshToken,
        };
    },
    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        userRole: (state) => state.user?.role || '',
        username: (state) => state.user?.username || '',
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
                        id: decoded.user_id,
                        username: decoded.username,
                        role: decoded.role,
                        company: {
                            id: decoded.company_id,
                            name: decoded.company_name
                        },
                        warehouse: {
                            id: decoded.warehouse_id,
                            name: decoded.warehouse_name
                        }
                    };
                } catch (e) {
                    console.error("Invalid token:", e);
                    this.logout();
                }
            }
        }
    }
});