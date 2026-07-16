import path from "node:path";
import { expect, test } from "@playwright/test";

const demoDir = path.resolve("public/demo-replays/close-2v2");
const incompleteDir = path.resolve("e2e/fixtures/incomplete-replay");

test("loads bundled replay and supports playback, selection, and follow", async ({ page }) => {
  const startedAt = Date.now();
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "3D Tactical Debrief" })).toBeVisible();
  expect(Date.now() - startedAt).toBeLessThan(5_000);

  await page.getByRole("button", { name: "Play", exact: true }).click();
  await expect(page.getByRole("button", { name: "Pause", exact: true })).toBeVisible();
  await page.keyboard.press("Space");
  await expect(page.getByRole("button", { name: "Play", exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Select team0_ranged_dps_0/ }).click();
  await expect(page.getByRole("button", { name: "Follow" })).toBeEnabled();
  await page.getByRole("heading", { name: "3D Tactical Debrief" }).click();
  await page.keyboard.press("f");
  await expect(page.getByRole("button", { name: "Follow" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("loads local fixtures without a manual picker and preserves replay on invalid input", async ({ page }) => {
  await page.goto("/");
  const chooser = page.getByLabel("Choose a CombatRL replay directory");
  await chooser.setInputFiles(demoDir);
  await expect(page.getByText("close-2v2", { exact: true })).toBeVisible();

  await chooser.setInputFiles(incompleteDir);
  await expect(page.getByRole("alert")).toContainText("missing frames.jsonl");
  await expect(page.getByRole("heading", { name: "3D Tactical Debrief" })).toBeVisible();
});

test("compact viewport keeps core controls available", async ({ page }) => {
  await page.setViewportSize({ width: 720, height: 900 });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Play", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open replay" })).toBeVisible();
  await expect(page.getByRole("slider", { name: "Replay timeline" })).toBeVisible();
});
