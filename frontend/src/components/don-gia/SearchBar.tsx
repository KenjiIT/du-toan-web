"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect, useState } from "react";

interface Props {
  onSearch: (q: string) => void;
  onChapterChange: (chapter: string) => void;
  onRegionChange: (region: string) => void;
  chapters: { code: string; name: string; count: number }[];
  region: string;
}

const REGIONS = [
  { value: "", label: "Định mức quốc gia" },
  { value: "HoChiMinh2023", label: "TP.HCM 2023" },
  { value: "HoChiMinh2023+2025", label: "TP.HCM 2023+2025" },
  { value: "HoChiMinh2025", label: "TP.HCM 2025" },
  { value: "HoChiMinh2016", label: "TP.HCM 2016" },
  { value: "HaNoi2023", label: "Hà Nội 2023" },
];

export function SearchBar({ onSearch, onChapterChange, onRegionChange, chapters, region }: Props) {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => onSearch(query), 300);
    return () => clearTimeout(timer);
  }, [query, onSearch]);

  return (
    <div className="flex gap-3 mb-4 flex-wrap">
      <Input
        placeholder="Tìm theo mã hoặc tên công việc..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="flex-1 min-w-[200px]"
      />
      <Select onValueChange={(v) => v && onChapterChange(v)} defaultValue="all">
        <SelectTrigger className="w-52">
          <SelectValue placeholder="Chương" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tất cả chương</SelectItem>
          {chapters.map((ch) => (
            <SelectItem key={ch.code} value={ch.code}>
              {ch.code} – {ch.name} ({ch.count})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={region} onValueChange={(v) => v && onRegionChange(v)}>
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Đơn giá vùng" />
        </SelectTrigger>
        <SelectContent>
          {REGIONS.map((r) => (
            <SelectItem key={r.value || "__norm"} value={r.value || "__norm"}>
              {r.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
