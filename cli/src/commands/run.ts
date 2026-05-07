import { Command } from "commander";
import { execFileSync } from "child_process";

export const runCommand = new Command("run")
  .description("Run a full pipeline (eval + guardrails)")
  .argument("<config>", "path to YAML config file")
  .option("-o, --output <dir>", "output directory", "./reports")
  .action((configPath: string, options: { output: string }) => {
    try {
      execFileSync("aigis", ["run", configPath, "--output", options.output], { stdio: "inherit" })
    } catch {
      console.log("Running full AIGIS pipeline...\n");
      execFileSync("python", ["-m", "aigis.cli.main", "run", configPath, "--output", options.output], { stdio: "inherit" })
    }
  });
