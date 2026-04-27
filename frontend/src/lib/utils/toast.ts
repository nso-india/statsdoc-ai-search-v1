import { toast } from 'svelte-sonner';

// Custom toast utilities with consistent styling
export const toastUtils = {
  // Error toasts that don't auto-close and have close button
  error: (message: string, options?: { description?: string; action?: any }) => {
    return toast.error(message, {
      duration: Infinity, // Don't auto-close error messages
      dismissible: true,
      description: options?.description || 'Click to dismiss this error message',
      action: options?.action,
      closeButton: true
    });
  },

  // Success toasts with normal auto-close
  success: (message: string, options?: { description?: string; action?: any }) => {
    return toast.success(message, {
      duration: 4000,
      dismissible: true,
      description: options?.description,
      action: options?.action,
      closeButton: true
    });
  },

  // Warning toasts with slightly longer duration
  warning: (message: string, options?: { description?: string; action?: any }) => {
    return toast.warning(message, {
      duration: 6000,
      dismissible: true,
      description: options?.description,
      action: options?.action,
      closeButton: true
    });
  },

  // Info toasts with normal duration
  info: (message: string, options?: { description?: string; action?: any }) => {
    return toast.info(message, {
      duration: 4000,
      dismissible: true,
      description: options?.description,
      action: options?.action,
      closeButton: true
    });
  }
};

// Backwards compatibility - replace existing toast calls gradually
export const errorToast = toastUtils.error;
export const successToast = toastUtils.success;
export const warningToast = toastUtils.warning;
export const infoToast = toastUtils.info;

