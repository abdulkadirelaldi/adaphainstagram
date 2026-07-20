"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/**
 * TanStack Query kabuğu. FE-1'de veri çekilmez — istemci burada kurulur ki
 * FE-3'te `docs/openapi.yaml`'dan üretilen tiplerle doğrudan bağlanabilsin.
 */
export function SorguSaglayici({ children }: { children: React.ReactNode }) {
  const [istemci] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Tarama sonuçları saniyelik değişmez; gereksiz istek maliyettir.
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={istemci}>{children}</QueryClientProvider>
  );
}
