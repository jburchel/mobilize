from flask import Blueprint, jsonify

def create_test_blueprint():
    """Create a test blueprint for testing purposes."""
    test_bp = Blueprint('test', __name__)

    @test_bp.route('/')
    def test_index():
        """Basic test endpoint."""
        return jsonify({'message': 'Test endpoint working'})

    @test_bp.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'healthy'})

    @test_bp.route('/error')
    def test_error():
        """Test error handling."""
        raise Exception('Test error')

    return test_bp 