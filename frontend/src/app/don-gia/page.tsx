"use client";

import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchDonGia, getChapters } from "@/lib/api";
import { SearchBar } from "@/components/don-gia/SearchBar";
import { ItemTable } from "@/components/don-gia/ItemTable";

export default function DonGiaPage() {
  const [q, setQ] = useState("");
  const [chapter, setChapter] = useState("all");
  const [region, setRegion] = useState("__norm");
  const [page, setPage] = useState(1);
  const limit = 20;

  const regionParam = region === "__norm" ? undefined : region;

  const chaptersQuery = useQuery({
    queryKey: ["chapters"],
    queryFn: () => getChapters(),
  });

  const searchQuery = useQuery({
    queryKey: ["don-gia", q, chapter, region, page],
    queryFn: () =>
      searchDonGia({
        q: q || undefined,
        chapter: chapter === "all" ? undefined : chapter,
        region: regionParam,
        page,
        limit,
      }),
  });

  const handleSearch = useCallback((query: string) => {
    setQ(query);
    setPage(1);
  }, []);

  const handleChapterChange = useCallback((ch: string) => {
    setChapter(ch);
    setPage(1);
  }, []);

  const handleRegionChange = useCallback((r: string) => {
    setRegion(r);
    setPage(1);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Tra cứu đơn giá</h1>
      <SearchBar
        onSearch={handleSearch}
        onChapterChange={handleChapterChange}
        onRegionChange={handleRegionChange}
        chapters={chaptersQuery.data || []}
        region={region}
      />
      {searchQuery.isLoading ? (
        <div className="text-center py-8 text-muted-foreground">
          Đang tải...
        </div>
      ) : searchQuery.error ? (
        <div className="text-center py-8 text-destructive">
          Lỗi kết nối API. Hãy đảm bảo backend đang chạy tại localhost:8000.
        </div>
      ) : searchQuery.data ? (
        <ItemTable
          items={searchQuery.data.items}
          total={searchQuery.data.total}
          page={searchQuery.data.page}
          limit={searchQuery.data.limit}
          onPageChange={setPage}
          region={regionParam}
        />
      ) : null}
    </div>
  );
}
