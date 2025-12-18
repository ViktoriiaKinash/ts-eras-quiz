import React, { useState } from "react";
import { useNavigate } from "react-router";
import { Container, Box, TextField, Button, Typography } from "@mui/material";

export default function QuizPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleGetEra() {
    setError(null);
    setLoading(true);
    try {
      const url = new URL(
        "https://backend-75096019526.europe-central2.run.app/api/quiz"
      );
      //   if (email) url.searchParams.set("email", email);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();
      // Navigate to results and pass data in state
      navigate("/results", { state: data });
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Box display="flex" flexDirection="column" gap={2}>
        <Typography variant="h5">Get Taylor Era</Typography>
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
        />
        <Button variant="contained" onClick={handleGetEra} disabled={loading}>
          {loading ? "Getting..." : "Get era"}
        </Button>
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
      </Box>
    </Container>
  );
}
