/**
 * API Service for MagicScanner Backend
 * Handles all communication with the FastAPI backend
 */

// IMPORTANT: Update this URL after deploying to Railway!
// Local development: Use your computer's local IP (not localhost)
// Production: Use your Railway URL

const API_CONFIG = {
  // For local development, find your local IP:
  // Mac: System Preferences > Network
  // Run in terminal: ipconfig getifaddr en0
  LOCAL_URL: 'http://192.168.1.5:8000', // UPDATE THIS with your local IP
  
  // After deploying to Railway, update this:
  PRODUCTION_URL: 'https://magic-scanner-backend-production.up.railway.app', // UPDATE THIS
  
  // Switch between local and production
  USE_LOCAL: false, // Set to false when using Railway
};

// Get the active API URL
const getApiUrl = () => {
  return API_CONFIG.USE_LOCAL ? API_CONFIG.LOCAL_URL : API_CONFIG.PRODUCTION_URL;
};

/**
 * Scan an image containing multiple Magic cards
 * @param {string} imageUri - URI of the image to scan
 * @param {string} scanMode - 'default' or 'pro' scan mode
 * @returns {Promise<Object>} Scan results
 */
export const scanCards = async (imageUri, scanMode = 'default') => {
  try {
    const apiUrl = getApiUrl();
    console.log('Sending request to:', apiUrl);
    console.log('Scan mode:', scanMode);

    // Create form data
    const formData = new FormData();

    // Extract filename from URI
    const filename = imageUri.split('/').pop();
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';

    formData.append('file', {
      uri: imageUri,
      name: filename || 'photo.jpg',
      type: type,
    });

    // Send request with scan_mode parameter
    const response = await fetch(`${apiUrl}/scan?scan_mode=${scanMode}`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'multipart/form-data',
      },
      body: formData,
      timeout: 30000, // 30 second timeout
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error:', response.status, errorText);
      throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('API Response:', data);

    if (!data.success) {
      throw new Error(data.message || 'Scan failed');
    }

    return data;

  } catch (error) {
    console.error('Error scanning cards:', error);
    
    // Provide more helpful error messages
    if (error.message.includes('Network request failed')) {
      throw new Error('Network error - cannot connect to backend. Check your API URL.');
    } else if (error.message.includes('timeout')) {
      throw new Error('Request timeout - backend is taking too long to respond.');
    }
    
    throw error;
  }
};

/**
 * Identify a single card from an image
 * @param {string} imageUri - URI of the image
 * @returns {Promise<Object>} Card identification result
 */
export const identifySingleCard = async (imageUri) => {
  try {
    const apiUrl = getApiUrl();

    const formData = new FormData();
    const filename = imageUri.split('/').pop();
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';

    formData.append('file', {
      uri: imageUri,
      name: filename || 'photo.jpg',
      type: type,
    });

    const response = await fetch(`${apiUrl}/identify-single`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'multipart/form-data',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error identifying card:', error);
    throw error;
  }
};

/**
 * Check backend health status
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const apiUrl = getApiUrl();
    
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      timeout: 5000,
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
};

/**
 * Get database statistics
 * @returns {Promise<Object>} Database stats
 */
export const getDatabaseStats = async () => {
  try {
    const apiUrl = getApiUrl();
    
    const response = await fetch(`${apiUrl}/database/stats`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Stats request failed: ${response.status}`);
    }

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error getting database stats:', error);
    throw error;
  }
};

/**
 * Test backend connection
 * Useful for debugging connection issues
 * @returns {Promise<boolean>} True if backend is reachable
 */
export const testConnection = async () => {
  try {
    const apiUrl = getApiUrl();
    console.log('Testing connection to:', apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      timeout: 5000,
    });

    return response.ok;

  } catch (error) {
    console.error('Connection test failed:', error);
    return false;
  }
};

// Export API config for settings/debugging
export const getApiConfig = () => ({
  currentUrl: getApiUrl(),
  useLocal: API_CONFIG.USE_LOCAL,
  localUrl: API_CONFIG.LOCAL_URL,
  productionUrl: API_CONFIG.PRODUCTION_URL,
});
