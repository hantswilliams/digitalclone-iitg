import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';

// Types
interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (credentials: { username: string; password: string }) => Promise<void>;
  register: (userData: {
    username: string;
    email: string;
    password: string;
    confirm_password: string;
    first_name: string;
    last_name: string;
    department?: string;
    title?: string;
    role?: string;
  }) => Promise<void>;
  logout: () => void;
  updateProfile: (profileData: { username?: string; email?: string }) => Promise<void>;
  changePassword: (passwordData: { currentPassword: string; newPassword: string }) => Promise<void>;
  clearError: () => void;
}

// Initial state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Action types
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  LOAD_USER_START: 'LOAD_USER_START',
  LOAD_USER_SUCCESS: 'LOAD_USER_SUCCESS',
  LOAD_USER_FAILURE: 'LOAD_USER_FAILURE',
  REGISTER_START: 'REGISTER_START',
  REGISTER_SUCCESS: 'REGISTER_SUCCESS',
  REGISTER_FAILURE: 'REGISTER_FAILURE',
  UPDATE_PROFILE_START: 'UPDATE_PROFILE_START',
  UPDATE_PROFILE_SUCCESS: 'UPDATE_PROFILE_SUCCESS',
  UPDATE_PROFILE_FAILURE: 'UPDATE_PROFILE_FAILURE',
  CHANGE_PASSWORD_START: 'CHANGE_PASSWORD_START',
  CHANGE_PASSWORD_SUCCESS: 'CHANGE_PASSWORD_SUCCESS',
  CHANGE_PASSWORD_FAILURE: 'CHANGE_PASSWORD_FAILURE',
  CLEAR_ERROR: 'CLEAR_ERROR',
} as const;

type AuthAction = 
  | { type: typeof AUTH_ACTIONS.LOGIN_START }
  | { type: typeof AUTH_ACTIONS.LOGIN_SUCCESS; payload: User }
  | { type: typeof AUTH_ACTIONS.LOGIN_FAILURE; payload: string }
  | { type: typeof AUTH_ACTIONS.LOGOUT }
  | { type: typeof AUTH_ACTIONS.LOAD_USER_START }
  | { type: typeof AUTH_ACTIONS.LOAD_USER_SUCCESS; payload: User }
  | { type: typeof AUTH_ACTIONS.LOAD_USER_FAILURE; payload: string }
  | { type: typeof AUTH_ACTIONS.REGISTER_START }
  | { type: typeof AUTH_ACTIONS.REGISTER_SUCCESS; payload: User }
  | { type: typeof AUTH_ACTIONS.REGISTER_FAILURE; payload: string }
  | { type: typeof AUTH_ACTIONS.UPDATE_PROFILE_START }
  | { type: typeof AUTH_ACTIONS.UPDATE_PROFILE_SUCCESS; payload: User }
  | { type: typeof AUTH_ACTIONS.UPDATE_PROFILE_FAILURE; payload: string }
  | { type: typeof AUTH_ACTIONS.CHANGE_PASSWORD_START }
  | { type: typeof AUTH_ACTIONS.CHANGE_PASSWORD_SUCCESS }
  | { type: typeof AUTH_ACTIONS.CHANGE_PASSWORD_FAILURE; payload: string }
  | { type: typeof AUTH_ACTIONS.CLEAR_ERROR };

// Reducer function
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
    case AUTH_ACTIONS.REGISTER_START:
    case AUTH_ACTIONS.LOAD_USER_START:
    case AUTH_ACTIONS.UPDATE_PROFILE_START:
    case AUTH_ACTIONS.CHANGE_PASSWORD_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
    case AUTH_ACTIONS.REGISTER_SUCCESS:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOAD_USER_SUCCESS:
    case AUTH_ACTIONS.UPDATE_PROFILE_SUCCESS:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_FAILURE:
    case AUTH_ACTIONS.REGISTER_FAILURE:
    case AUTH_ACTIONS.LOAD_USER_FAILURE:
    case AUTH_ACTIONS.UPDATE_PROFILE_FAILURE:
    case AUTH_ACTIONS.CHANGE_PASSWORD_FAILURE:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case AUTH_ACTIONS.CHANGE_PASSWORD_SUCCESS:
      return {
        ...state,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };

    default:
      return state;
  }
};

// Create context
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// AuthProvider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Load user on app startup
  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOAD_USER_START });
      const token = localStorage.getItem('token');
      
      if (!token) {
        dispatch({ type: AUTH_ACTIONS.LOAD_USER_FAILURE, payload: 'No token found' });
        return;
      }

      const response = await authService.getProfile();
      dispatch({ type: AUTH_ACTIONS.LOAD_USER_SUCCESS, payload: response.data.user });
    } catch (error: any) {
      dispatch({ 
        type: AUTH_ACTIONS.LOAD_USER_FAILURE, 
        payload: error.response?.data?.message || 'Failed to load user' 
      });
      localStorage.removeItem('token');
    }
  };

  const login = async (credentials: { username: string; password: string }) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      const response = await authService.login(credentials);
      
      localStorage.setItem('token', response.data.token);
      dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: response.data.user });
    } catch (error: any) {
      dispatch({ 
        type: AUTH_ACTIONS.LOGIN_FAILURE, 
        payload: error.response?.data?.message || 'Login failed' 
      });
      throw error;
    }
  };

  const register = async (userData: {
    username: string;
    email: string;
    password: string;
    confirm_password: string;
    first_name: string;
    last_name: string;
    department?: string;
    title?: string;
    role?: string;
  }) => {
    try {
      dispatch({ type: AUTH_ACTIONS.REGISTER_START });
      const response = await authService.register(userData);
      
      localStorage.setItem('token', response.data.token);
      dispatch({ type: AUTH_ACTIONS.REGISTER_SUCCESS, payload: response.data.user });
    } catch (error: any) {
      dispatch({ 
        type: AUTH_ACTIONS.REGISTER_FAILURE, 
        payload: error.response?.data?.message || 'Registration failed' 
      });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  const updateProfile = async (profileData: { username?: string; email?: string }) => {
    try {
      dispatch({ type: AUTH_ACTIONS.UPDATE_PROFILE_START });
      const response = await authService.updateProfile(profileData);
      dispatch({ type: AUTH_ACTIONS.UPDATE_PROFILE_SUCCESS, payload: response.data.user });
    } catch (error: any) {
      dispatch({ 
        type: AUTH_ACTIONS.UPDATE_PROFILE_FAILURE, 
        payload: error.response?.data?.message || 'Profile update failed' 
      });
      throw error;
    }
  };

  const changePassword = async (passwordData: { currentPassword: string; newPassword: string }) => {
    try {
      dispatch({ type: AUTH_ACTIONS.CHANGE_PASSWORD_START });
      await authService.changePassword(passwordData);
      dispatch({ type: AUTH_ACTIONS.CHANGE_PASSWORD_SUCCESS });
    } catch (error: any) {
      dispatch({ 
        type: AUTH_ACTIONS.CHANGE_PASSWORD_FAILURE, 
        payload: error.response?.data?.message || 'Password change failed' 
      });
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
