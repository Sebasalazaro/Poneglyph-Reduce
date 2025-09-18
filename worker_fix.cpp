// Correct worker registration code

void Worker::registerSelf() {
    auto [cpuUsage, memUsage] = getSystemMetrics();

    // Prefer gRPC if available
    if (grpc) {
        std::string wid;
        int poll_ms = 1000;
        // Generate unique worker name using hostname + random suffix
        std::string workerName = "poneglyph-worker-" + std::to_string(rand() % 1000);
        bool ok = grpc->RegisterWorker(workerName, /*capacity*/ 2, wid, &poll_ms);
        if (ok && !wid.empty()) {
            workerId = wid;
            std::cout << "[gRPC] Registered as " << workerId << " (poll=" << poll_ms << "ms)\n";
        } else {
            std::cerr << "[gRPC] Register failed, falling back to HTTP.\n";
        }
    }

    if (workerId.empty()) {
        // HTTP fallback
        std::string workerName = "poneglyph-worker-" + std::to_string(rand() % 1000);
        std::ostringstream registrationPayload;
        registrationPayload << "{"
                << "\"name\":\"" << workerName << "\","
                << "\"capacity\":2," // Capacidad de tareas concurrentes