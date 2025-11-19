import asyncio
import json
import websockets
import random

# Lưu trữ trạng thái game: { "player_id": { x, y, angle, skin, score, ... } }
GAME_STATE = {}

# Lưu trữ kết nối socket: { websocket_object: player_id }
CONNECTED_CLIENTS = {}

async def broadcast_state():
    """Gửi toàn bộ trạng thái game cho tất cả người chơi đang kết nối"""
    if not CONNECTED_CLIENTS:
        return
    
    # Chuyển dữ liệu thành JSON
    message = json.dumps({"type": "update", "data": GAME_STATE})
    
    # Gửi cho tất cả (bỏ qua các socket đã đóng)
    websockets_to_remove = set()
    for ws in list(CONNECTED_CLIENTS.keys()):
        try:
            await ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            websockets_to_remove.add(ws)
            
    # Dọn dẹp các kết nối đã chết
    for ws in websockets_to_remove:
        await unregister(ws)

async def unregister(websocket):
    """Xóa người chơi khi ngắt kết nối"""
    if websocket in CONNECTED_CLIENTS:
        player_id = CONNECTED_CLIENTS[websocket]
        del CONNECTED_CLIENTS[websocket]
        if player_id in GAME_STATE:
            del GAME_STATE[player_id]
        print(f"Player {player_id} disconnected")

async def handler(websocket):
    """Xử lý từng kết nối client"""
    # Tạo ID ngẫu nhiên cho người chơi mới
    player_id = f"user_{random.randint(1000, 9999)}"
    CONNECTED_CLIENTS[websocket] = player_id
    print(f"Player {player_id} connected")

    try:
        async for message in websocket:
            data = json.loads(message)
            
            # Nếu client gửi dữ liệu di chuyển
            if data.get("type") == "move":
                # Cập nhật thông tin vào GAME_STATE
                player_info = data.get("info")
                GAME_STATE[player_id] = player_info
                
                # Sau khi cập nhật, broadcast ngay (hoặc có thể dùng loop riêng để tối ưu)
                await broadcast_state()

            # Nếu client báo chết
            elif data.get("type") == "die":
                # Xử lý logic chết (ví dụ: xóa khỏi state tạm thời hoặc reset điểm)
                pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket)

async def main():
    print("Server started on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # Chạy mãi mãi

if __name__ == "__main__":
    asyncio.run(main())
