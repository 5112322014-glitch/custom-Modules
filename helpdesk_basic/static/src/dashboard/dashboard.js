/** @odoo-module **/
import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

class HelpdeskDashboard extends Component {
    static template = "helpdesk_basic.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        // References to the two canvas elements in the template
        this.stageCanvas = useRef("stageCanvas");
        this.categoryCanvas = useRef("categoryCanvas");
        this.charts = [];
        // Numbers shown in the boxes at the top
        this.state = useState({ total: 0, open: 0, urgent: 0, done: 0 });

        onWillStart(async () => {
            // Load the Chart.js library that ships with Odoo
            await loadBundle("web.chartjs_lib");
            await this.loadData();
        });
        onMounted(() => this.renderCharts());
        onWillUnmount(() => this.charts.forEach((chart) => chart.destroy()));
    }

    async loadData() {
        const model = "helpdesk.basic.ticket";
        const openDomain = [["stage", "in", ["new", "in_progress"]]];
        this.state.total = await this.orm.searchCount(model, []);
        this.state.open = await this.orm.searchCount(model, openDomain);
        this.state.urgent = await this.orm.searchCount(model, [...openDomain, ["priority", "=", "3"]]);
        this.state.done = await this.orm.searchCount(model, [["stage", "in", ["resolved", "closed"]]]);
        // Grouped counts used by the charts
        this.stageGroups = await this.orm.readGroup(model, [], ["stage"], ["stage"]);
        this.categoryGroups = await this.orm.readGroup(model, [], ["category"], ["category"]);
    }

    renderCharts() {
        const names = {
            new: "New", in_progress: "In Progress", resolved: "Resolved", closed: "Closed",
            hardware: "Hardware", software: "Software", network: "Network", other: "Other",
        };
        const label = (value) => names[value] || value || "Not set";
        const count = (group) => group.__count || 0;
        const colors = ["#714B67", "#017E84", "#F4A261", "#E76F51", "#2A9D8F", "#8D99AE"];

        // Bar chart: tickets per stage
        this.charts.push(new Chart(this.stageCanvas.el, {
            type: "bar",
            data: {
                labels: this.stageGroups.map((g) => label(g.stage)),
                datasets: [{
                    label: "Tickets",
                    data: this.stageGroups.map(count),
                    backgroundColor: colors,
                }],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        }));

        // Doughnut chart: tickets per category
        this.charts.push(new Chart(this.categoryCanvas.el, {
            type: "doughnut",
            data: {
                labels: this.categoryGroups.map((g) => label(g.category)),
                datasets: [{
                    data: this.categoryGroups.map(count),
                    backgroundColor: colors,
                }],
            },
        }));
    }

    // Open the ticket list filtered by the clicked box
    openList(title, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "helpdesk.basic.ticket",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }
}

registry.category("actions").add("helpdesk_basic.dashboard", HelpdeskDashboard);
