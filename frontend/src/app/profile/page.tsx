"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { updateProfile, changePassword } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [profileMsg, setProfileMsg] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [pwdMsg, setPwdMsg] = useState("");
  const [pwdError, setPwdError] = useState("");
  const [pwdSaving, setPwdSaving] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  if (isLoading || !user) {
    return <div className="p-6">Đang tải...</div>;
  }

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg("");
    setProfileError("");
    setProfileSaving(true);
    try {
      await updateProfile({
        full_name: fullName || undefined,
        email: email || undefined,
      });
      setProfileMsg("Cập nhật thông tin thành công");
    } catch (err: unknown) {
      setProfileError(err instanceof Error ? err.message : "Cập nhật thất bại");
    } finally {
      setProfileSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdMsg("");
    setPwdError("");

    if (newPassword !== confirmNewPassword) {
      setPwdError("Mật khẩu mới xác nhận không khớp");
      return;
    }

    if (newPassword.length < 6) {
      setPwdError("Mật khẩu mới phải có ít nhất 6 ký tự");
      return;
    }

    setPwdSaving(true);
    try {
      await changePassword(oldPassword, newPassword);
      setPwdMsg("Đổi mật khẩu thành công");
      setOldPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err: unknown) {
      setPwdError(err instanceof Error ? err.message : "Đổi mật khẩu thất bại");
    } finally {
      setPwdSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Thông tin tài khoản</h1>

      <Card>
        <CardHeader>
          <CardTitle>Thông tin cá nhân</CardTitle>
          <CardDescription>Cập nhật thông tin tài khoản của bạn</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            {profileMsg && (
              <div className="text-sm text-green-600 bg-green-50 border border-green-200 rounded-md p-3">
                {profileMsg}
              </div>
            )}
            {profileError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
                {profileError}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tên đăng nhập</label>
              <Input value={user.username} disabled />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Vai trò</label>
              <Input value={user.role === "admin" ? "Quản trị viên" : "Người dùng"} disabled />
            </div>
            <div className="space-y-2">
              <label htmlFor="fullName" className="text-sm font-medium">
                Họ và tên
              </label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nhập họ và tên"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Nhập email"
              />
            </div>
            <Button type="submit" disabled={profileSaving}>
              {profileSaving ? "Đang lưu..." : "Cập nhật"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Đổi mật khẩu</CardTitle>
          <CardDescription>Thay đổi mật khẩu đăng nhập</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {pwdMsg && (
              <div className="text-sm text-green-600 bg-green-50 border border-green-200 rounded-md p-3">
                {pwdMsg}
              </div>
            )}
            {pwdError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
                {pwdError}
              </div>
            )}
            <div className="space-y-2">
              <label htmlFor="oldPassword" className="text-sm font-medium">
                Mật khẩu hiện tại
              </label>
              <Input
                id="oldPassword"
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="Nhập mật khẩu hiện tại"
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="newPassword" className="text-sm font-medium">
                Mật khẩu mới
              </label>
              <Input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Ít nhất 6 ký tự"
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="confirmNewPassword" className="text-sm font-medium">
                Xác nhận mật khẩu mới
              </label>
              <Input
                id="confirmNewPassword"
                type="password"
                value={confirmNewPassword}
                onChange={(e) => setConfirmNewPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu mới"
                required
              />
            </div>
            <Button type="submit" disabled={pwdSaving}>
              {pwdSaving ? "Đang đổi..." : "Đổi mật khẩu"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
