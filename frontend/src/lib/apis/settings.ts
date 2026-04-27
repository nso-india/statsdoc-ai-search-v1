import { WEBUI_API_BASE_URL } from '$lib/constants';

const handleApiError = (err: any) => {
  console.error(err);
  return err.detail || err.message || err;
};

export const getAllConfigs = async (token: string) => {
  let error = null;
  const res = await fetch(`${WEBUI_API_BASE_URL}/settings/configs/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = handleApiError(err);
      return null;
    });
  if (error) throw error;
  return res;
};

export const getNamespaceConfig = async (token: string, namespace: string) => {
  let error = null;
  const res = await fetch(`${WEBUI_API_BASE_URL}/settings/configs/${namespace}/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = handleApiError(err);
      return null;
    });
  if (error) throw error;
  return res;
};

export const updateNamespaceConfig = async (token: string, namespace: string, config_data: object) => {
  let error = null;
  const res = await fetch(`${WEBUI_API_BASE_URL}/settings/configs/${namespace}/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ config_data })
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = handleApiError(err);
      return null;
    });
  if (error) throw error;
  return res;
};
