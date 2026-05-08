"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function ReportRedirect() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  useEffect(() => {
    if (id) router.replace(`/result/${id}`);
  }, [id, router]);
  return null;
}
