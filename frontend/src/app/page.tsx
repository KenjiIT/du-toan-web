import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const stats = [
  { title: "Công việc", value: "13,000+", desc: "Mã đơn giá trong hệ thống" },
  { title: "Định mức", value: "38,000+", desc: "Hàng hao phí tài nguyên" },
  { title: "Vật tư", value: "3,100+", desc: "Loại vật tư/nhân công/máy" },
  { title: "Tỉnh/ngành", value: "252", desc: "Bộ đơn giá địa phương" },
];

export default function Home() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dự Toán Xây Dựng</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <Card key={s.title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {s.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{s.value}</div>
              <p className="text-xs text-muted-foreground">{s.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Bắt đầu</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong>Tra cứu đơn giá:</strong> Tìm công việc theo mã hoặc tên,
            xem chi tiết định mức và đơn giá tổng hợp.
          </p>
          <p>
            <strong>Lập dự toán:</strong> Tạo dự toán mới, thêm công việc và
            khối lượng, hệ thống tự động tính giá.
          </p>
          <p>
            <strong>Vật tư:</strong> Quản lý giá vật tư theo kỳ, cập nhật giá
            thị trường.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
