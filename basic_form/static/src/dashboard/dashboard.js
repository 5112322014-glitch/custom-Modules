/** @odoo-module **/
import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

class BasicFormDashboard extends Component {
    static template = "basic_form.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        // References to the two canvas elements in the template
        this.deptCanvas = useRef("deptCanvas");
        this.statusCanvas = useRef("statusCanvas");
        this.charts = [];
        // Numbers shown in the boxes at the top
        this.state = useState({ total: 0, active: 0, onLeave: 0, interns: 0 });

        onWillStart(async () => {
            // Load the Chart.js library that ships with Odoo
            await loadBundle("web.chartjs_lib");
            await this.loadData();
        });
        onMounted(() => this.renderCharts());
        onWillUnmount(() => this.charts.forEach((chart) => chart.destroy()));
    }

    async loadData() {
        const model = "basic.form";
        this.state.total = await this.orm.searchCount(model, []);
        this.state.active = await this.orm.searchCount(model, [["status", "=", "active"]]);
        this.state.onLeave = await this.orm.searchCount(model, [["status", "=", "on_leave"]]);
        this.state.interns = await this.orm.searchCount(model, [["employment_type", "=", "intern"]]);
        // Grouped counts used by the charts
        this.deptGroups = await this.orm.readGroup(model, [], ["department"], ["department"]);
        this.statusGroups = await this.orm.readGroup(model, [], ["status"], ["status"]);
    }

    renderCharts() {
        const label = (value) => value || "Not set";
        const count = (group) => group.__count || 0;
        const colors = ["#714B67", "#017E84", "#F4A261", "#E76F51", "#2A9D8F", "#8D99AE"];

        // Bar chart: employees per department
        this.charts.push(new Chart(this.deptCanvas.el, {
            type: "bar",
            data: {
                labels: this.deptGroups.map((g) => label(g.department)),
                datasets: [{
                    label: "Employees",
                    data: this.deptGroups.map(count),
                    backgroundColor: colors,
                }],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        }));

        // Doughnut chart: employees per status
        this.charts.push(new Chart(this.statusCanvas.el, {
            type: "doughnut",
            data: {
                labels: this.statusGroups.map((g) => label(g.status)),
                datasets: [{
                    data: this.statusGroups.map(count),
                    backgroundColor: colors,
                }],
            },
        }));
    }

    // Open the employee list filtered by the clicked box
    openList(title, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "basic.form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }
}

registry.category("actions").add("basic_form.dashboard", BasicFormDashboard);
