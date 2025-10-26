(function () {
  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const numberFormatter = new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const balanceTotal = document.getElementById("balance-total");
  const balanceAvailable = document.getElementById("balance-available");
  const balanceInPositions = document.getElementById("balance-in-positions");
  const balancePnL = document.getElementById("balance-pnl");
  const balancePnLPercent = document.getElementById("balance-pnl-percent");
  const lastUpdatedEl = document.getElementById("last-updated");
  const positionsTableBody = document.querySelector("#positions-table tbody");
  const tradesTableBody = document.querySelector("#trades-table tbody");

  let balanceChart;

  function formatCurrency(value) {
    return currencyFormatter.format(value || 0);
  }

  function formatNumber(value) {
    return numberFormatter.format(value || 0);
  }

  function formatPercent(value) {
    return percentFormatter.format((value || 0) / 100);
  }

  function renderSummary(balance) {
    balanceTotal.textContent = formatCurrency(balance.total);
    balanceAvailable.textContent = formatCurrency(balance.available);
    balanceInPositions.textContent = formatCurrency(balance.in_positions);

    balancePnL.textContent = formatCurrency(balance.profit_loss);
    balancePnL.classList.toggle("pnl-positive", balance.profit_loss >= 0);
    balancePnL.classList.toggle("pnl-negative", balance.profit_loss < 0);

    balancePnLPercent.textContent = formatPercent(balance.profit_loss_pct);
    balancePnLPercent.classList.toggle("pnl-positive", balance.profit_loss >= 0);
    balancePnLPercent.classList.toggle("pnl-negative", balance.profit_loss < 0);
  }

  function renderPositions(positions) {
    positionsTableBody.innerHTML = "";

    if (!positions || positions.length === 0) {
      positionsTableBody.innerHTML =
        '<tr><td colspan="7" class="text-center text-muted py-4">No open positions.</td></tr>';
      return;
    }

    positions.forEach((position) => {
      const row = document.createElement("tr");
      const isProfit = position.unrealized_pnl >= 0;

      row.innerHTML = `
        <td>${position.symbol}</td>
        <td class="text-center">
          <span class="badge rounded-pill ${position.side === "long" ? "bg-success" : "bg-danger"}">
            ${position.side.toUpperCase()}
          </span>
        </td>
        <td class="text-end">${formatNumber(position.quantity)}</td>
        <td class="text-end">${formatCurrency(position.entry_price)}</td>
        <td class="text-end">${formatCurrency(position.current_price)}</td>
        <td class="text-end ${isProfit ? "pnl-positive" : "pnl-negative"}">${formatCurrency(position.unrealized_pnl)}</td>
        <td class="text-end">${position.liquidation_price ? formatCurrency(position.liquidation_price) : "-"}</td>
      `;

      positionsTableBody.appendChild(row);
    });
  }

  function renderTrades(trades) {
    tradesTableBody.innerHTML = "";

    if (!trades || trades.length === 0) {
      tradesTableBody.innerHTML =
        '<tr><td colspan="7" class="text-center text-muted py-4">No trades yet.</td></tr>';
      return;
    }

    trades.forEach((trade) => {
      const row = document.createElement("tr");
      const timestamp = trade.timestamp
        ? new Date(trade.timestamp).toLocaleString()
        : "--";
      row.innerHTML = `
        <td>${timestamp}</td>
        <td class="text-truncate" style="max-width: 160px" title="${trade.order_id || ""}">${
        trade.order_id || "-"
      }</td>
        <td>${trade.symbol || "-"}</td>
        <td class="text-center">
          <span class="badge rounded-pill ${trade.side === "buy" ? "bg-success" : "bg-danger"}">
            ${(trade.side || "-").toUpperCase()}
          </span>
        </td>
        <td class="text-end">${formatNumber(trade.quantity || 0)}</td>
        <td class="text-end">${formatCurrency(trade.price || 0)}</td>
        <td>${trade.type ? trade.type.toUpperCase() : "-"}</td>
      `;

      tradesTableBody.appendChild(row);
    });
  }

  function renderBalanceChart(history) {
    const ctx = document.getElementById("balance-chart");
    const labels = history.map((item) => new Date(item.timestamp));
    const data = history.map((item) => item.total);

    if (balanceChart) {
      balanceChart.data.labels = labels;
      balanceChart.data.datasets[0].data = data;
      balanceChart.update();
      return;
    }

    balanceChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Portfolio Balance",
            data,
            fill: true,
            borderColor: "#0d6efd",
            backgroundColor: "rgba(13, 110, 253, 0.15)",
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          x: {
            type: "time",
            time: {
              tooltipFormat: "MMM d, yyyy HH:mm",
              displayFormats: {
                hour: "MMM d HH:mm",
                day: "MMM d",
                minute: "HH:mm",
              },
            },
            ticks: {
              autoSkip: true,
              maxTicksLimit: 6,
            },
          },
          y: {
            ticks: {
              callback: (value) => formatCurrency(value),
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: (context) => `Balance: ${formatCurrency(context.parsed.y)}`,
            },
          },
        },
      },
    });
  }

  function updateLastUpdated(timestamp) {
    if (!timestamp) {
      lastUpdatedEl.textContent = "--";
      return;
    }
    const formatted = new Date(timestamp).toLocaleString();
    lastUpdatedEl.textContent = formatted;
  }

  function renderDashboard(data) {
    if (!data) {
      return;
    }
    renderSummary(data.balance || {});
    renderPositions(data.positions || []);
    renderTrades(data.trade_history || []);
    renderBalanceChart(data.balance_history || []);
    updateLastUpdated(data.last_updated);
  }

  async function refreshDashboard() {
    try {
      const response = await fetch("/api/dashboard");
      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard data: ${response.status}`);
      }
      const data = await response.json();
      renderDashboard(data);
    } catch (error) {
      console.error(error);
    }
  }

  renderDashboard(window.dashboardData);
  setInterval(refreshDashboard, 15000);
})();
