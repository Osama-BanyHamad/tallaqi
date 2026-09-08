"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "@/lib/api";

export default function Index() {
  const r = useRouter();
  useEffect(() => { r.replace(getSession() ? "/dashboard" : "/login"); }, [r]);
  return null;
}
