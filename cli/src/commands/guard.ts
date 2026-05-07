import { Command } from "commander";
import { execSync } from "child_process";
import chalk from "chalk";

export const guardCommand = new Command("guard")
  .description("Check text against guardrails")
  .argument("<text>", "text to check")
  .option("--no-jailbreak", "skip jailbreak detection")
  .option("--no-toxicity", "skip toxicity check")
  .action((text: string, options: { jailbreak: boolean; toxicity: boolean }) => {
    const args = [`"${text}"`];
    if (!options.jailbreak) args.push("--no-jailbreak");
    if (!options.toxicity) args.push("--no-toxicity");

    try {
      execSync(`aigis guard ${args.join(" ")}`, { stdio: "inherit" });
    } catch {
      console.log(chalk.cyan("\nAIGIS Guardrail Check"));
      console.log(chalk.gray("─".repeat(50)));

      const checks = [];
      if (options.jailbreak) {
        const hasJailbreak = /ignore|DAN|bypass|override/i.test(text);
        checks.push({
          name: "jailbreak_detection",
          passed: !hasJailbreak,
          score: hasJailbreak ? 0.8 : 0.0,
        });
      }
      if (options.toxicity) {
        const toxicWords = ["hate", "kill", "stupid", "idiot"];
        const found = toxicWords.filter((w) => text.toLowerCase().includes(w));
        checks.push({
          name: "toxicity",
          passed: found.length === 0,
          score: found.length / toxicWords.length,
        });
      }

      for (const check of checks) {
        const icon = check.passed ? chalk.green("PASS") : chalk.red("FAIL");
        console.log(`  [${icon}] ${check.name}: ${check.score.toFixed(2)}`);
      }

      const allPassed = checks.every((c) => c.passed);
      if (allPassed) {
        console.log(chalk.green("\nAll guardrails passed."));
      } else {
        console.log(chalk.red("\nSome guardrails triggered!"));
        process.exit(1);
      }
    }
  });
