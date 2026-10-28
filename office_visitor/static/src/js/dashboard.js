/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class VisitorDashboard extends Component {
    static template = "office_visitor.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: {} });
        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "office.visitor", "get_dashboard_data", []
        );
        this.state.loading = false;
    }

    openList(title, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "office.visitor",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }

    openToday() {
        this.openList("Today's Visitors",
            [["visit_date", "=", this.state.data.today]]);
    }

    openInside() {
        this.openList("Inside Now", [["state", "=", "checked_in"]]);
    }

    openCheckedOut() {
        this.openList("Checked Out Today", [
            ["state", "=", "checked_out"],
            ["visit_date", "=", this.state.data.today],
        ]);
    }

    openLast10() {
        this.openList("Last 10 Days",
            [["visit_date", ">=", this.state.data.date_from]]);
    }

    openDay(date) {
        this.openList("Visitors on " + date, [["visit_date", "=", date]]);
    }

    openVisitor(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "office.visitor",
            res_id: id,
            views: [[false, "form"]],
        });
    }
}

registry.category("actions").add("office_visitor.dashboard", VisitorDashboard);
