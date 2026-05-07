import { Command } from "commander";
import { execSync } from "child_process";

export const runCommand = new Command("run")
  .description("Run a full pipeline (eval + guardrails)")
  .argument("<config>", "path to YAML config file")
  .option("-o, --output <dir>", "output directory", "./reports")
  .action((configPath: string, options: { output: string }) => {
    try {
      execSync(`aigis run "${configPath}" --output "${options.output}"`, {
        stdio: "inherit",
      });
    } catch {
      console.log("Running full AIGIS pipeline...\n");
      execSync(
        `python -m aigis.cli.main run "${configPath}" --output "${options.output}"`,
        { stdio: "inherit" }
      );
    }
  });
