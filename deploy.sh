if [[ -f archive.zip ]]; then
	echo "removing archive.zip"
	rm archive.zip
fi
zip -r archive.zip . -x "**/__pycache__/*" -x "*.pyc" ".*" -x "*/.*" "logs/*" "__pycache__/*" "zip*.sh" "test*.py"
scp -i ~/.ssh/j@dbn.pem archive.zip ec2-user@ec2-3-92-221-120.compute-1.amazonaws.com:/home/ec2-user/app
