import os
import sys
import click
import pytest
import coverage
from typing import Optional, List

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger

logger = get_logger('test_utils')

def run_tests(
    test_type: str = 'all', 
    verbose: bool = False, 
    data_path: Optional[str] = None, 
    coverage_flag: bool = False, 
    output_format: str = 'html'
) -> int:
    """
    Comprehensive test runner with configurable options.
    
    :param test_type: Type of tests to run
    :param verbose: Enable verbose output
    :param data_path: Custom path for test data
    :param coverage_flag: Generate coverage report
    :param output_format: Format for coverage report
    :return: Test exit code
    """
    logger.info(f"Starting test run: type={test_type}, verbose={verbose}")
    
    # Configure pytest arguments
    pytest_args = ['-v'] if verbose else []
    
    # Select test directories based on test type
    if test_type == 'unit':
        pytest_args.extend(['tests/unit'])
    elif test_type == 'integration':
        pytest_args.extend(['tests/integration'])
    elif test_type == 'e2e':
        pytest_args.extend(['tests/e2e'])
    elif test_type == 'performance':
        pytest_args.extend(['tests/performance'])
    else:  # all tests
        pytest_args.extend(['tests'])
    
    # Add custom data path if provided
    if data_path:
        os.environ['TEST_DATA_PATH'] = data_path
    
    # Configure coverage
    if coverage_flag:
        cov = coverage.Coverage(source=['app', 'utils'])
        cov.start()
    
    try:
        # Run tests
        exit_code = pytest.main(pytest_args)
        
        # Generate coverage report
        if coverage_flag:
            cov.stop()
            cov.save()
            
            if output_format == 'html':
                cov.html_report(directory='coverage_report')
            elif output_format == 'xml':
                cov.xml_report(outfile='coverage.xml')
            elif output_format == 'json':
                cov.json_report(outfile='coverage.json')
            
            logger.info(f"Coverage report generated in {output_format} format")
        
        return exit_code
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

@click.command()
@click.option('--type', type=click.Choice(['unit', 'integration', 'e2e', 'performance', 'all']), default='all', help="Type of test to run")
@click.option('--verbose', is_flag=True, help="Increase output verbosity")
@click.option('--data-path', type=click.Path(exists=True), default='data/test_data', help="Path to custom test data directory")
@click.option('--coverage', is_flag=True, help="Generate code coverage reports")
@click.option('--output-format', type=click.Choice(['html', 'xml', 'json']), default='html', help="Specify report format")
def test_cli(type, verbose, data_path, coverage, output_format):
    """
    CLI interface for running tests with various configurations.
    """
    result = run_tests(
        test_type=type, 
        verbose=verbose, 
        data_path=data_path, 
        coverage_flag=coverage, 
        output_format=output_format
    )
    sys.exit(result)

if __name__ == '__main__':
    test_cli()
