export const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
};

export const formatNumber = (value: number | undefined | null) => {
    if (value === undefined || value === null) return '0';
    return new Intl.NumberFormat('en-IN').format(value);
};
