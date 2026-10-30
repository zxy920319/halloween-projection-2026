using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

// Connects to the desktop pose publisher and forwards only the newest message to PoseReceiver.
public sealed class PoseWebSocketClient : MonoBehaviour
{
    [SerializeField] private PoseReceiver receiver;
    [SerializeField] private string url = "ws://127.0.0.1:8766/poses";
    [SerializeField, Min(0.5f)] private float reconnectDelaySeconds = 2f;

    private const int MaxMessageBytes = 256 * 1024;
    private readonly ConcurrentQueue<string> inbox = new ConcurrentQueue<string>();
    private CancellationTokenSource cts;

    private void OnEnable()
    {
        cts = new CancellationTokenSource();
        _ = RunAsync(cts.Token);
    }

    private void OnDisable()
    {
        cts?.Cancel();
        cts?.Dispose();
        cts = null;
    }

    private void Update()
    {
        string latest = null;
        while (inbox.TryDequeue(out string message))
        {
            latest = message;
        }
        if (latest != null && receiver != null)
        {
            receiver.ApplyJson(latest);
        }
    }

    private async Task RunAsync(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            try
            {
                using (var socket = new ClientWebSocket())
                {
                    await socket.ConnectAsync(new Uri(url), token);
                    Debug.Log($"Pose socket connected: {url}");
                    await ReceiveLoopAsync(socket, token);
                }
            }
            catch (OperationCanceledException)
            {
                return;
            }
            catch (Exception exception)
            {
                Debug.LogWarning($"Pose socket error: {exception.Message}");
            }

            try
            {
                await Task.Delay(TimeSpan.FromSeconds(reconnectDelaySeconds), token);
            }
            catch (OperationCanceledException)
            {
                return;
            }
        }
    }

    private async Task ReceiveLoopAsync(ClientWebSocket socket, CancellationToken token)
    {
        var buffer = new byte[16 * 1024];
        var text = new StringBuilder();
        while (socket.State == WebSocketState.Open && !token.IsCancellationRequested)
        {
            text.Clear();
            WebSocketReceiveResult result;
            do
            {
                result = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), token);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    return;
                }
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    text.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                }
                if (text.Length > MaxMessageBytes)
                {
                    Debug.LogWarning("Pose message too large; reconnecting.");
                    return;
                }
            } while (!result.EndOfMessage);

            if (text.Length > 0)
            {
                inbox.Enqueue(text.ToString());
            }
        }
    }
}
