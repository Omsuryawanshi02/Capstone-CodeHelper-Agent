import { API_BASE_URL } from './client';
import { HealthState } from '../types';

export async function fetchHealth(): Promise<HealthState> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    if (!response.ok) {
      return {
        status: 'unhealthy',
        backendRunning: false,
        adkReachable: false,
        adkAppName: 'code_helper',
        configValid: false,
      };
    }

    const data = await response.json();
    return {
      status: data.status,
      backendRunning: Boolean(data.backend_running),
      adkReachable: Boolean(data.adk_reachable),
      adkAppName: data.adk_app_name || 'code_helper',
      configValid: Boolean(data.config_valid),
    };
  } catch (err) {
    return {
      status: 'unhealthy',
      backendRunning: false,
      adkReachable: false,
      adkAppName: 'code_helper',
      configValid: false,
    };
  }
}
