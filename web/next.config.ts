import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Depo çok dilli: kökte Python projesi, burada Next uygulaması. Kök çıkarımını
  // sabitlemezsek Next dışarıdaki bir lockfile'ı kök sanıyor.
  outputFileTracingRoot: path.join(__dirname),
  typedRoutes: true,
};

export default nextConfig;
