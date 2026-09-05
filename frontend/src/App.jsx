import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  // =========================
  // State
  // =========================
  const [result, setResult] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recovering, setRecovering] = useState(null);

  // =========================
  // Get payments from database
  // =========================
  const fetchPayments = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/payments"
      );

      console.log("PAYMENTS FROM DATABASE:", response.data);

      setPayments(response.data);
    } catch (error) {
      console.error("PAYMENTS API ERROR:", error);
    }
  };

  // Load payments when dashboard opens
  useEffect(() => {
    fetchPayments();
  }, []);

  // =========================
  // Dynamic Dashboard Stats
  // =========================
  const totalPayments = payments.length;

  const failedPayments = payments.filter(
    (payment) => payment.status === "failed"
  ).length;

  const recoveredPayments = payments.filter(
    (payment) => payment.status === "recovered"
  ).length;

  const recoveryRate =
    totalPayments > 0
      ? ((recoveredPayments / totalPayments) * 100).toFixed(1)
      : 0;

  // =========================
  // Analyze Selected Payment with AI
  // =========================
  const analyzePayment = async (payment) => {
    setLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/analyze-payment",
        {
          transaction_id: payment.transaction_id,
          customer: payment.customer,
          amount: payment.amount,
          status: payment.status,
          reason: payment.reason,
        }
      );

      console.log("AI RESPONSE:", response.data);

      setResult({
        ...response.data,
        customer: payment.customer,
      });
    } catch (error) {
      console.error("AI API ERROR:", error);
      alert("Failed to recover payment. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // Recover Payment
  // =========================
  const recoverPayment = async (transactionId) => {
    setRecovering(transactionId);

    try {
      const response = await axios.put(
        `http://127.0.0.1:8000/payments/${transactionId}/recover`
      );

      console.log("RECOVERY RESPONSE:", response.data);

      // Refresh payments from database
      await fetchPayments();

      // Clear AI result if it belongs to recovered payment
      if (
        result &&
        result.transaction_id === transactionId
      ) {
        setResult(null);
      }

    } catch (error) {
      console.error("RECOVERY API ERROR:", error);
    } finally {
      setRecovering(null);
    }
  };

  // =========================
  // Dashboard UI
  // =========================
  return (
    <div className="dashboard">

      {/* Header */}
      <header className="header">
        <div>
          <h1>PayRecover AI</h1>
          <p>AI-Powered Payment Recovery Dashboard</p>
        </div>
      </header>

      <main className="container">

        {/* =========================
            Dynamic Overview Cards
        ========================= */}
        <section className="cards">

          <div className="card">
            <h3>Total Payments</h3>
            <p className="number">
              {totalPayments}
            </p>
          </div>

          <div className="card">
            <h3>Failed Payments</h3>
            <p className="number">
              {failedPayments}
            </p>
          </div>

          <div className="card">
            <h3>Recovered Payments</h3>
            <p className="number">
              {recoveredPayments}
            </p>
          </div>

          <div className="card">
            <h3>Recovery Rate</h3>
            <p className="number">
              {recoveryRate}%
            </p>
          </div>

        </section>

        {/* =========================
            Recent Payments
        ========================= */}
        <section className="panel">

          <h2>Recent Payments</h2>

          <table>

            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>

              {payments.map((payment) => (

                <tr key={payment.transaction_id}>

                  <td>
                    {payment.transaction_id}
                  </td>

                  <td>
                    {payment.customer}
                  </td>

                  <td>
                    ₹{payment.amount}
                  </td>

                  <td>
                    {payment.reason}
                  </td>

                  <td>
                    <span 
                    className={
                      payment.status ==="recovered"
                      ? "status recovered"
                      : "status failed"
                    }
                    >
                       {payment.status}
                    </span>
                  </td>

                  <td>

                    {/* Analyze button */}
                    <button
                      onClick={() =>
                        analyzePayment(payment)
                      }
                      disabled={loading}
                    >
                      {loading
                        ? "Analyzing..."
                        : "Analyze"}
                    </button>

                    {/* Recover button */}
                    {payment.status === "failed" && (

                      <button
                        onClick={() =>
                          recoverPayment(
                            payment.transaction_id
                          )
                        }
                        disabled={
                          recovering ===
                          payment.transaction_id
                        }
                      >
                        {recovering ===
                        payment.transaction_id
                          ? "Recovering..."
                          : "Mark as Recovered"}
                      </button>

                    )}

                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        </section>

        {/* =========================
            Live AI Analysis Result
        ========================= */}
        {result && (

          <section className="panel">

            <h2>🤖 Live AI Analysis</h2>

            <div className="recommendation">

              <h3>
                {result.transaction_id} —{" "}
                {result.customer}
              </h3>

              <p>
                <strong>Status:</strong>{" "}
                {result.status}
              </p>

              <p>
                <strong>Priority:</strong>{" "}
                {result.priority}
              </p>

              <p className="recomendation-text">
                <strong>Recommendation:</strong>
                <br />
                {result.recommendation}
              </p>

              <p className="customer-message">
                <strong>Customer Message:</strong>
                <br />
                {result.customer_message}
              </p>

            </div>

          </section>

        )}

      </main>

    </div>
  );
}

export default App;