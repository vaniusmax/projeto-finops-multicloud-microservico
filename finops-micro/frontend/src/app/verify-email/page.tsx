import { Suspense } from "react";

import { VerifyEmailPage } from "@/components/auth/VerifyEmailPage";

export default function VerifyEmailRoute() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailPage />
    </Suspense>
  );
}
