export default [
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        fetch: "readonly",
        setTimeout: "readonly",
        setInterval: "readonly",
        SpeechSynthesisUtterance: "readonly",
        SpeechRecognition: "readonly",
        webkitSpeechRecognition: "readonly",
        Event: "readonly",
        console: "readonly",
      },
    },
    rules: {
      "no-const-assign": "error",
      "no-empty": "error",
      "no-unused-vars": ["error", { "vars": "all", "args": "none" }],
    },
  },
];
