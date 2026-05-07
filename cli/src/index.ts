#!/usr/bin/env node

import { Command } from "commander";
import { evalCommand } from "./commands/eval.js";
import { guardCommand } from "./commands/guard.js";
import { runCommand } from "./commands/run.js";
import { dashboardCommand } from "./commands/dashboard.js";
import { initCommand } from "./commands/init.js";

const program = new Command();

program
  .name("aigis")
  .description("AIGIS — AI Guardrail & Integration System")
  .version("0.1.0");

program.addCommand(evalCommand);
program.addCommand(guardCommand);
program.addCommand(runCommand);
program.addCommand(dashboardCommand);
program.addCommand(initCommand);

program.parse();
