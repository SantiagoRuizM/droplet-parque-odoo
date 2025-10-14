/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { browser } from "../../core/browser/browser";
import { registry } from "../../core/registry";

export function preferencesItem(env) {
    return {
        type: "item",
        id: "settings",
        description: _t("Perfil"),
        callback: async function () {
            const actionDescription = await env.services.orm.call("res.users", "action_get");
            actionDescription.res_id = env.services.user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 50,
    };
}

function logOutItem(env) {
    return {
        type: "item",
        id: "logout",
        description: _t("Log out"),
        callback: async () => {
            // Step 1: Get session info to retrieve BYPASS_API_TOKEN from server
            let bearerToken = null;

            try {
                const sessionResponse = await fetch('/web/session/get_session_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {}
                    })
                });

                const sessionData = await sessionResponse.json();
                bearerToken = sessionData.result?.bypass_api_token;
            } catch (error) {
                console.error("❌ Error getting session info:", error);
            }

            // Step 2: Reset bypass credentials to generic user BEFORE logout
            if (bearerToken) {
                try {
                    console.log("🔄 Resetting bypass credentials before logout...");

                    const resetCredentials = await fetch("/api/bypass/credentials", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${bearerToken}`
                        },
                        body: JSON.stringify({
                            jsonrpc: "2.0",
                            method: "call",
                            params: {
                                user: "usuario_generico",
                                password: "XXXXXXX"
                            }
                        })
                    });

                    if (resetCredentials.ok) {
                        const resetResult = await resetCredentials.json();
                        console.log("✅ Bypass credentials reset successfully:", resetResult);
                    } else {
                        console.error("❌ Failed to reset credentials. Status:", resetCredentials.status);
                    }

                    // Wait to ensure the credentials update completes
                    await new Promise(resolve => setTimeout(resolve, 500));

                } catch (error) {
                    console.error("❌ Error resetting bypass credentials:", error);
                }
            }

            // Step 3: Destroy session
            try {
                console.log("🔓 Destroying session...");
                await fetch("/web/session/logout");
                console.log("✅ Session destroyed");
                await new Promise(resolve => setTimeout(resolve, 300));
            } catch (error) {
                console.error("❌ Error during logout:", error);
            }

            // Step 4: Redirect to localhost:3000
            console.log("🔀 Redirecting to http://localhost:3000");
            window.location.href = "http://localhost:3000";
        },
        sequence: 70,
    };
}

registry
    .category("user_menuitems")
    .add("profile", preferencesItem)
    .add("log_out", logOutItem);
