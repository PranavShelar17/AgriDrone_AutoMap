// Frontend configuration module

export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api/v1',
  appName: 'AgriDrone AutoMap',
  version: '0.1.0',
  defaultPollingIntervalMs: 5000,
} as const;
