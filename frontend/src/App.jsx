// // Then, install dependencies: npm install tailwindcss postcss autoprefixer lucide-react recharts

import React, { useState, useRef, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Send,
  Bot,
  User,
  BarChart2,
  Loader2,
  AlertTriangle,
} from "lucide-react";

// Make sure this URL is correct for your setup
const API_URL = "http://localhost:8000";

const App = () => {
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [history, isLoading]);

  const exampleQueries = [
    "What are the top five portfolios of our wealth members?",
    "Give me the breakup of portfolio values per relationship manager.",
    "Which clients have a high risk appetite?",
    "Tell me the top relationship managers in my firm",
    "Which clients are the highest holders of RELIANCE stock?",
  ];

  const handleQuerySubmit = async (question) => {
    if (!question.trim() || isLoading) return;

    const userMessage = {
      from: "user",
      data: { type: "text", data: question },
    };
    // Add user message and clear input immediately
    setHistory((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setQuery("");

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const errorData = await response.json(); // FastAPI often returns JSON on error
        throw new Error(
          `HTTP error! status: ${response.status}, message: ${
            errorData.detail || "Unknown error"
          }`
        );
      }

      const result = await response.json();
      const botMessage = { from: "bot", data: result };
      setHistory((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("API call failed:", error);
      const errorMessage = {
        from: "bot",
        data: {
          type: "error",
          data: `Failed to get response. Is the backend server running? \nError: ${error.message}`,
        },
      };
      setHistory((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // FIX: Clearer logic. Sets the input field and submits the query.
  const handleExampleQueryClick = (exQuery) => {
    if (isLoading) return;
    setQuery(exQuery);
    handleQuerySubmit(exQuery);
  };

  const renderBotResponse = (message) => {
    const { type, data } = message.data;

    switch (type) {
      case "text":
        return <p className="text-gray-800 dark:text-gray-200">{data}</p>;

      case "table":
        if (!data || !Array.isArray(data) || data.length === 0) {
          return (
            <p className="text-gray-800 dark:text-gray-200">
              No data available to display.
            </p>
          );
        }
        const headers = data.length > 0 ? Object.keys(data[0]) : [];
        return (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-gray-100 dark:bg-gray-900/50">
                <tr>
                  {headers.map((header) => (
                    <th
                      key={header}
                      className="px-4 py-2 border-b-2 border-gray-200 dark:border-gray-600 font-semibold text-gray-700 dark:text-gray-300 capitalize"
                    >
                      {/* Simple camelCase to Title Case conversion */}
                      {header
                        .replace(/([A-Z])/g, " $1")
                        .replace(/^./, (str) => str.toUpperCase())}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr
                    key={i}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    {headers.map((header) => (
                      <td
                        key={header}
                        className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200"
                      >
                        {typeof row[header] === "number"
                          ? row[header].toLocaleString()
                          : String(row[header])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case "chart":
        if (!data || !Array.isArray(data) || data.length === 0) {
          return (
            <p className="text-gray-800 dark:text-gray-200">
              No data available for the chart.
            </p>
          );
        }
        return (
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <BarChart
                data={data}
                margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="name" />
                <YAxis
                  tickFormatter={(value) =>
                    new Intl.NumberFormat("en-US", {
                      notation: "compact",
                      compactDisplay: "short",
                    }).format(value)
                  }
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(31, 41, 55, 0.9)",
                    borderColor: "rgba(55, 65, 81, 0.8)",
                    borderRadius: "0.5rem",
                  }}
                  labelStyle={{ color: "#d1d5db" }}
                  formatter={(value) =>
                    new Intl.NumberFormat("en-US").format(value)
                  }
                />
                <Legend />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case "error":
        return (
          <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-lg">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <p className="whitespace-pre-wrap">{data}</p>
          </div>
        );

      default:
        return (
          <p className="text-gray-800 dark:text-gray-200">
            Received an unknown response type.
          </p>
        );
    }
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-900 min-h-screen flex flex-col items-center p-4 font-sans text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-4xl flex flex-col h-[calc(100vh-2rem)]">
        <div className="mb-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <BarChart2 className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">
                Natural Language Data Agent
              </h1>
              {/* FIX: Changed MySQL to PostgreSQL */}
              <p className="text-gray-600 dark:text-gray-400">
                Query your PostgreSQL and MongoDB databases using plain English.
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-6 p-4 bg-white dark:bg-gray-800 rounded-xl shadow-inner border border-gray-200 dark:border-gray-700">
          {history.length === 0 && (
            <div className="space-y-2 mb-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Try an example:
              </p>
              <div className="flex flex-wrap gap-2">
                {exampleQueries.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => handleExampleQueryClick(ex)}
                    disabled={isLoading}
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}
          {history.map((message, index) => (
            <div
              key={index}
              className={`flex items-start gap-4 ${
                message.from === "user" ? "justify-end" : ""
              }`}
            >
              {message.from === "bot" && (
                <div className="p-2 bg-blue-100 dark:bg-gray-700 rounded-full self-start">
                  <Bot className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              )}
              <div
                className={`max-w-xl rounded-lg p-3 ${
                  message.from === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 w-full"
                }`}
              >
                {message.from === "user" ? (
                  <p>{message.data.data}</p>
                ) : (
                  renderBotResponse(message)
                )}
              </div>
              {message.from === "user" && (
                <div className="p-2 bg-gray-200 dark:bg-gray-600 rounded-full">
                  <User className="h-6 w-6" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-100 dark:bg-gray-700 rounded-full">
                <Bot className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="rounded-lg p-3 bg-gray-100 dark:bg-gray-700 flex items-center space-x-2 text-gray-700 dark:text-gray-300">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="mt-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleQuerySubmit(query);
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question like: 'What is the total portfolio value?'"
              className="flex-1 w-full px-4 py-2 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default App;
