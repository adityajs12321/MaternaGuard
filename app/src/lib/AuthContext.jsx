import React, { createContext, useState, useContext, useEffect } from 'react';
import { maternaguardApi } from '@/api/maternaguard';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [doctorToken, setDoctorToken] = useState(localStorage.getItem('mg_doctor_token') || null);
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [isLoadingPublicSettings, setIsLoadingPublicSettings] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [appPublicSettings, setAppPublicSettings] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  const buildDefaultUser = () => {
    const existingDeviceId = localStorage.getItem('mg_device_id');
    const deviceId = existingDeviceId || crypto.randomUUID();
    if (!existingDeviceId) {
      localStorage.setItem('mg_device_id', deviceId);
    }
    return {
      device_id: deviceId,
      role: 'patient',
      full_name: 'MaternaGuard User',
      email: '',
      abha_id: localStorage.getItem('mg_abha_id') || '',
    };
  };

  const hydrateUser = (rawUser) => {
    const base = buildDefaultUser();
    if (!rawUser) return base;
    const next = { ...base, ...rawUser };
    if (!next.device_id) {
      next.device_id = base.device_id;
    }
    return next;
  };

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setIsLoadingAuth(true);
      setAuthError(null);

      const saved = localStorage.getItem('mg_user');
      const parsed = saved ? JSON.parse(saved) : null;
      setUser(hydrateUser(parsed));

      try {
        const health = await maternaguardApi.health();
        setHealthStatus(health);
        setAppPublicSettings({ api_base_url: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' });
      } catch (err) {
        setAuthError({ type: 'backend_unreachable', message: err.message });
      }

      setIsLoadingAuth(false);
    } catch (error) {
      setAuthError({ type: 'unknown', message: error.message || 'Initialization failed' });
      setUser(buildDefaultUser());
      setIsLoadingAuth(false);
    }
  };

  const updateUser = (nextUser) => {
    localStorage.setItem('mg_user', JSON.stringify(nextUser));
    if (nextUser.abha_id !== undefined) {
      localStorage.setItem('mg_abha_id', nextUser.abha_id || '');
    }
    setUser(nextUser);
  };

  const loginDoctor = async (username, password) => {
    const response = await maternaguardApi.loginDoctor(username, password);
    localStorage.setItem('mg_doctor_token', response.access_token);
    setDoctorToken(response.access_token);
    const doctorUser = {
      ...(user || buildDefaultUser()),
      role: 'admin',
      full_name: username,
    };
    updateUser(doctorUser);
    return response;
  };

  const logout = () => {
    localStorage.removeItem('mg_doctor_token');
    setDoctorToken(null);
    if (user) {
      const patientUser = { ...user, role: 'patient' };
      updateUser(patientUser);
    }
  };

  const navigateToLogin = () => {
    window.location.href = '/provider';
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      setUser: updateUser,
      doctorToken,
      isAuthenticated, 
      isLoadingAuth,
      isLoadingPublicSettings,
      authError,
      appPublicSettings,
      healthStatus,
      loginDoctor,
      logout,
      navigateToLogin,
      checkAppState: initializeAuth,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
