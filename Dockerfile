FROM python:3.11-slim

WORKDIR /sandbox

RUN pip install --no-cache-dir \
    pandas numpy matplotlib seaborn scipy \
    statsmodels scikit-learn

CMD ["python"]