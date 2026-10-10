package com.example

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import java.io.IOException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonPrimitive

class OpenSourceProvider(
    private val baseUrl: String,
    private val apiKey: String,
    private val modelName: String
) : ModelProvider {
    override val name: String = "Configured model ($modelName)"

    private val client = OpenSourceClient(baseUrl)

    override suspend fun generateStream(request: ModelRequest): Flow<String> = flow {
        val messages = mutableListOf<OpenAiMessage>()
        
        // Add system instruction
        val fullInstruction = request.systemInstruction + 
            if (request.context.isNotEmpty()) "\n\n[HOST CODEBASE CONTEXT]\n${request.context}" else ""
        messages.add(OpenAiMessage(role = "system", content = fullInstruction))
        
        // Add history
        request.history.forEach { msg ->
            messages.add(OpenAiMessage(
                role = if (msg.isFromUser) "user" else "assistant",
                content = msg.text
            ))
        }

        val openAiRequest = OpenAiRequest(
            model = modelName,
            messages = messages,
            stream = true
        )

        val response = client.service.generateChatStream("Bearer $apiKey", openAiRequest)
        
        response.use { body ->
            body.byteStream().bufferedReader().use { reader ->
                var completed = false
                while (true) {
                    currentCoroutineContext().ensureActive()
                    val line = reader.readLine() ?: break
                    if (!line.startsWith("data:")) continue
                    val jsonStr = line.substring(5).trim()
                    if (jsonStr == "[DONE]") { completed = true; break }
                    if (jsonStr.isEmpty()) continue
                    val chunk = Json.parseToJsonElement(jsonStr).jsonObject
                    if (chunk["error"] != null) throw IOException("Model provider returned an error")
                    val delta = chunk["choices"]?.jsonArray
                        ?.getOrNull(0)?.jsonObject?.get("delta")?.jsonObject
                    val content = delta?.get("content")?.jsonPrimitive?.content ?: ""
                    if (content.isNotEmpty()) emit(content)
                }
                if (!completed) throw IOException("Model stream ended before its completion marker")
            }
        }
    }.flowOn(Dispatchers.IO)
}
