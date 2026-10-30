import { expect, type Locator, type Page } from "@playwright/test"

import { API_URL, FRONTEND_URL } from "../constants"
import { api } from "./api"

/** A company's new API key with `permissions`: its id and the whole key. */
export async function createKey(
  page: Page,
  companyId: string,
  name: string,
  permissions: string[]
) {
  return api<{ id: string; key: string }>(page, "POST", `/v1/manage/keys?company_id=${companyId}`, {
    name,
    expiry: "1",
    permissions,
  })
}

/** A key form's ticks in `form`: "Select all" first, then one per permission in the order the
 * API lists them for the company (its API settings' groups), found with `tick(permission)`; and
 * the permissions a new key starts with (`defaults`). */
export async function permissionTicks(page: Page, companyId: string, form: Locator) {
  const settings = await api<{
    permission_groups: Record<string, string[]>
    default_permissions: string[]
  }>(page, "GET", `/v1/manage?company_id=${companyId}`)
  const permissions = Object.values(settings.permission_groups).flat()
  const all = form.getByRole("checkbox")

  return {
    all,
    count: permissions.length + 1,
    defaults: settings.default_permissions,
    tick: (permission: string) => all.nth(permissions.indexOf(permission) + 1),
  }
}

/** Deletes a company's API key. */
export async function deleteKey(page: Page, companyId: string, keyId: string) {
  await api(page, "DELETE", `/v1/manage/keys/${keyId}?company_id=${companyId}`)
}

/** Adds a note to an interview through the public API, as the key. */
export async function keyNote(page: Page, key: string, interviewId: string, text: string) {
  const response = await page.request.post(`${API_URL}/v1/interviews/${interviewId}/notes`, {
    headers: { Authorization: `Bearer ${key}` },
    data: { text },
  })
  expect(response.status(), `note through the API -> ${response.status()}`).toBe(201)
}

/** Calls an MCP tool as the key, as an AI agent on a server does; fails on a refusal. */
export async function mcpTool(page: Page, key: string, name: string, args: object) {
  const response = await page.request.post(`${FRONTEND_URL}/mcp`, {
    headers: {
      Authorization: `Bearer ${key}`,
      Accept: "application/json, text/event-stream",
      "MCP-Protocol-Version": "2025-06-18",
    },
    data: { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args } },
  })
  expect(response.status(), `MCP ${name} -> ${response.status()}`).toBe(200)
  const { result } = await response.json()
  expect(result.isError, `MCP ${name}: ${JSON.stringify(result)}`).toBe(false)
}
