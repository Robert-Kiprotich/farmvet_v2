import React from 'react';
import Swal from 'sweetalert2';

// ── SweetAlert Component ──────────────────────────────────────────────────────
interface SweetAlertProps {
  type: 'info' | 'warning' | 'error' | 'success' | 'question' | 'confirm';
  title?: string;
  message?: string;
  buttonText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  showCancelButton?: boolean;
  confirmButtonColor?: string;
  cancelButtonColor?: string;
  timer?: number;
  className?: string;
  children?: React.ReactNode;
  confirmButtonText?: string;
  cancelButtonText?: string;
  showConfirmButton?: boolean;
}

const alertConfigs = {
  info: {
    icon: 'info' as const,
    confirmButtonColor: '#0d6efd',
  },
  warning: {
    icon: 'warning' as const,
    confirmButtonColor: '#ffc107',
  },
  error: {
    icon: 'error' as const,
    confirmButtonColor: '#dc3545',
  },
  success: {
    icon: 'success' as const,
    confirmButtonColor: '#198754',
  },
  question: {
    icon: 'question' as const,
    confirmButtonColor: '#6c757d',
  },
  confirm: {
    icon: 'warning' as const,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
  },
};

const SweetAlert: React.FC<SweetAlertProps> = ({
  type,
  title = '',
  message = '',
  buttonText = 'OK',
  onConfirm,
  onCancel,
  showCancelButton = false,
  confirmButtonColor,
  cancelButtonColor = '#6c757d',
  timer,
  className = '',
  children,
  confirmButtonText,
  cancelButtonText = 'Cancel',
  showConfirmButton = true,
}) => {
  const config = alertConfigs[type];

  const handleClick = async () => {
    // For confirm type, show confirmation dialog
    if (type === 'confirm') {
      const result = await Swal.fire({
        title: title || 'Are you sure?',
        text: message || "You won't be able to revert this!",
        icon: config.icon,
        showCancelButton: true,
        confirmButtonColor: confirmButtonColor || config.confirmButtonColor,
        cancelButtonColor: cancelButtonColor || config.cancelButtonColor,
        confirmButtonText: confirmButtonText || 'Yes, delete it!',
        cancelButtonText: cancelButtonText,
        timer,
        allowOutsideClick: false,
      });

      if (result.isConfirmed && onConfirm) {
        onConfirm();
        // Show success message after deletion
        await Swal.fire({
          title: 'Deleted!',
          text: 'Your file has been deleted.',
          icon: 'success',
          confirmButtonColor: '#198754',
          timer: 2000,
        });
      } else if (result.dismiss === Swal.DismissReason.cancel && onCancel) {
        onCancel();
        // Show cancelled message
        await Swal.fire({
          title: 'Cancelled',
          text: 'Your imaginary file is safe :)',
          icon: 'error',
          confirmButtonColor: '#dc3545',
          timer: 2000,
        });
      }
      return;
    }

    // For other alert types
    if (!showConfirmButton) {
      // Show without confirm button (auto-close or just message)
      await Swal.fire({
        title: title || capitalizeFirstLetter(type),
        text: message,
        icon: config.icon,
        confirmButtonColor: confirmButtonColor || config.confirmButtonColor,
        timer: timer || 2000,
        showConfirmButton: false,
        allowOutsideClick: true,
      });
      if (onConfirm) onConfirm();
      return;
    }

    const result = await Swal.fire({
      title: title || capitalizeFirstLetter(type),
      text: message,
      icon: config.icon,
      confirmButtonText: buttonText,
      showCancelButton,
      cancelButtonText: cancelButtonText,
      confirmButtonColor: confirmButtonColor || config.confirmButtonColor,
      cancelButtonColor,
      timer,
      allowOutsideClick: false,
    });

    if (result.isConfirmed && onConfirm) {
      onConfirm();
    } else if (result.isDismissed && onCancel) {
      onCancel();
    }
  };

  const capitalizeFirstLetter = (str: string) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  // Don't render button if no children and not a button type
  if (!children && !showConfirmButton) {
    return null;
  }

  return (
    <button
      className={`btn btn-${type === 'confirm' ? 'danger' : type} ${className}`}
      onClick={handleClick}
      type="button"
    >
      {children || `${capitalizeFirstLetter(type)} Alert`}
    </button>
  );
};

// ── Individual Alert Components ──────────────────────────────────────────────
export const InfoAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="info" {...props} />
);

export const WarningAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="warning" {...props} />
);

export const ErrorAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="error" {...props} />
);

export const SuccessAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="success" {...props} />
);

export const QuestionAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="question" {...props} />
);

export const ConfirmAlert: React.FC<Omit<SweetAlertProps, 'type'>> = (props) => (
  <SweetAlert type="confirm" {...props} />
);

// ── Custom Alert Hook ────────────────────────────────────────────────────────
export const useSweetAlert = () => {
  const showAlert = async ({
    type,
    title,
    message,
    confirmButtonText = 'OK',
    cancelButtonText = 'Cancel',
    showCancelButton = false,
    confirmButtonColor,
    cancelButtonColor = '#6c757d',
    timer,
    onConfirm,
    onCancel,
  }: {
    type: 'info' | 'warning' | 'error' | 'success' | 'question';
    title?: string;
    message?: string;
    confirmButtonText?: string;
    cancelButtonText?: string;
    showCancelButton?: boolean;
    confirmButtonColor?: string;
    cancelButtonColor?: string;
    timer?: number;
    onConfirm?: () => void;
    onCancel?: () => void;
  }) => {
    const config = alertConfigs[type];
    
    const result = await Swal.fire({
      title: title || capitalizeFirstLetter(type),
      text: message,
      icon: config.icon,
      confirmButtonText,
      cancelButtonText,
      showCancelButton,
      confirmButtonColor: confirmButtonColor || config.confirmButtonColor,
      cancelButtonColor,
      timer,
      allowOutsideClick: false,
    });

    if (result.isConfirmed && onConfirm) {
      onConfirm();
    } else if (result.isDismissed && onCancel) {
      onCancel();
    }

    return result;
  };

  // Confirmation dialog
  const showConfirm = async ({
    title = 'Are you sure?',
    message = "You won't be able to revert this!",
    confirmButtonText = 'Yes, delete it!',
    cancelButtonText = 'Cancel',
    onConfirm,
    onCancel,
  }: {
    title?: string;
    message?: string;
    confirmButtonText?: string;
    cancelButtonText?: string;
    onConfirm?: () => void;
    onCancel?: () => void;
  }) => {
    const result = await Swal.fire({
      title,
      text: message,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText,
      cancelButtonText,
      allowOutsideClick: false,
    });

    if (result.isConfirmed) {
      if (onConfirm) onConfirm();
      await Swal.fire({
        title: 'Deleted!',
        text: 'Your file has been deleted.',
        icon: 'success',
        confirmButtonColor: '#198754',
        timer: 2000,
      });
      return true;
    } else if (result.dismiss === Swal.DismissReason.cancel) {
      if (onCancel) onCancel();
      await Swal.fire({
        title: 'Cancelled',
        text: 'Your imaginary file is safe :)',
        icon: 'error',
        confirmButtonColor: '#dc3545',
        timer: 2000,
      });
      return false;
    }
    return false;
  };

  const capitalizeFirstLetter = (str: string) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  return { showAlert, showConfirm };
};

// ── Quick Functions ──────────────────────────────────────────────────────────
export const showInfo = (message: string, title?: string, timer?: number) => {
  return Swal.fire({
    title: title || 'Info',
    text: message,
    icon: 'info',
    confirmButtonColor: '#0d6efd',
    timer: timer || 2000,
    timerProgressBar: true,
  });
};

export const showWarning = (message: string, title?: string, timer?: number) => {
  return Swal.fire({
    title: title || 'Warning',
    text: message,
    icon: 'warning',
    confirmButtonColor: '#ffc107',
    timer: timer || 2000,
    timerProgressBar: true,
  });
};

export const showError = (message: string, title?: string, timer?: number) => {
  return Swal.fire({
    title: title || 'Error',
    text: message,
    icon: 'error',
    confirmButtonColor: '#dc3545',
    timer: timer || 3000,
    timerProgressBar: true,
  });
};

export const showSuccess = (message: string, title?: string, timer?: number) => {
  return Swal.fire({
    title: title || 'Success',
    text: message,
    icon: 'success',
    confirmButtonColor: '#198754',
    timer: timer || 2000,
    timerProgressBar: true,
  });
};

export const showConfirm = async (
  message?: string,
  title?: string,
  confirmButtonText?: string,
  cancelButtonText?: string
) => {
  const result = await Swal.fire({
    title: title || 'Are you sure?',
    text: message || "You won't be able to revert this!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: confirmButtonText || 'Yes, delete it!',
    cancelButtonText: cancelButtonText || 'Cancel',
    allowOutsideClick: false,
  });

  if (result.isConfirmed) {
    await Swal.fire({
      title: 'Deleted!',
      text: 'Your file has been deleted.',
      icon: 'success',
      confirmButtonColor: '#198754',
      timer: 2000,
    });
    return true;
  } else if (result.dismiss === Swal.DismissReason.cancel) {
    await Swal.fire({
      title: 'Cancelled',
      text: 'Your imaginary file is safe :)',
      icon: 'error',
      confirmButtonColor: '#dc3545',
      timer: 2000,
    });
    return false;
  }
  return false;
};


export default SweetAlert;