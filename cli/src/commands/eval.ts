import { Command } from "commander";
import { readFileSync } from "fs";
import { resolve } from "path";
import { parse as parseYaml } from "yaml";
import { execSync } from "child_process";

export const evalCommand = new Command("eval")
  .description("Run evaluations defined in a YAML config")
  .argument("<config>", "path to YAML config file")
  .option("-o, --output <dir>", "output directory", "./reports")
  .option("-f, --format <fmt>", "output format: table, json, html", "table")
  .action(async (configPath: string, options: { output: string; format: string }) => {
    const absPath = resolve(configPath);
    const raw = readFileSync(absPath, "utf-8");
    const cfg = parseYaml(raw);

    console.log(`Running eval: ${cfg.name || "unnamed"}`);
    console.log(`Model: ${cfg.model?.provider}/${cfg.model?.model}`);
    console.log(`Tests: ${cfg.eval?.tests?.length || 0}`);
    console.log(`Prompts: ${cfg.eval?.prompts?.length || 0}`);
    console.log();

    try {
      const result = execSync(
        `aigis eval "${configPath}" --output "${options.output}" --format "${options.format}"`,
        { stdio: "inherit" }
      );
    } catch {
      console.error("\nFalling back to Python runner...");
    }
  });
