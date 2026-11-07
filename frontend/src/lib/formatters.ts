export function formatVND(amount: number | null | undefined): string {
  if (amount == null || amount === 0) return "-";
  return new Intl.NumberFormat("vi-VN").format(Math.round(amount)) + " đ";
}

export function formatNumber(n: number | null | undefined, decimals = 0): string {
  if (n == null) return "-";
  return new Intl.NumberFormat("vi-VN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n);
}
