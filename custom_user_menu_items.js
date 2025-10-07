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
        href: "http://localhost:3000",
        callback: () => {
            // Destruir sesión y redirigir a localhost:3000
            fetch("/web/session/logout").finally(() => {
                window.location.href = "http://localhost:3000";
            });
        },
        sequence: 70,
    };
}

registry
    .category("user_menuitems")
    .add("profile", preferencesItem)
    .add("log_out", logOutItem);
