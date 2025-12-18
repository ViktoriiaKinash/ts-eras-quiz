import React from "react";
import { useLocation, useNavigate } from "react-router";
import { Container, Box, Typography, Button } from "@mui/material";

export default function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state: any = location.state ?? {};
  const { era, image_url } = state;

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Box display="flex" flexDirection="column" gap={2} alignItems="center">
        <Typography variant="h5">Results</Typography>
        {era ? (
          <>
            <Typography variant="h6">Era: {era}</Typography>
            {image_url && (
              <img
                src={image_url}
                alt={era}
                style={{ maxWidth: "100%", borderRadius: 8 }}
              />
            )}
          </>
        ) : (
          <Typography>No result data available.</Typography>
        )}

        <Button variant="outlined" onClick={() => navigate(-1)}>
          Back
        </Button>
      </Box>
    </Container>
  );
}
