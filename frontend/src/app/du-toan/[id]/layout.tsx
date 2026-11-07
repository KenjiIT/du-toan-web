import { Suspense } from "react";

export function generateStaticParams() {
    return [{ id: "0" }];
}

export default function ProjectLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <Suspense fallback={<div className="p-8 text-muted-foreground">Đang tải...</div>}>{children}</Suspense>;
}
