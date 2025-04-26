
import grpc
from concurrent import futures
import engineproject_pb2
import engineproject_pb2_grpc
from app import __version__

class EngineServiceServicer(engineproject_pb2_grpc.EngineServiceServicer):
    def GetVersion(self, request, context):
        return engineproject_pb2.VersionReply(version=__version__)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    engineproject_pb2_grpc.add_EngineServiceServicer_to_server(EngineServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
