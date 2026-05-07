import { Command } from "commander";
import { execFileSync } from "child_process";
import { resolve } from "path";

export const dashboardCommand = new Command("dashboard")
  .description("Launch the AIGIS interactive dashboard")
  .option("-p, --port <port>", "port to serve on", "5173")
  .option("--host <host>", "host to bind to", "127.0.0.1")
  .action((options: { port: string; host: string }) => {
    const dashboardDir = resolve(import.meta.dirname, "../../../dashboard");

    console.log("Starting AIGIS Dashboard...");
    console.log(`Open http://${options.host}:${options.port}`);

    try {
      execFileSync("npx", ["vite", "--port", options.port, "--host", options.host], { cwd: dashboardDir, stdio: "inherit" })
    } catch {
      console.log("Installing dashboard dependencies...");
      execFileSync("npm", ["install"], { cwd: dashboardDir, stdio: "inherit" });
      execFileSync("npx", ["vite", "--port", options.port, "--host", options.host], { cwd: dashboardDir, stdio: "inherit" })
    }
  });
