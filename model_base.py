
import os

from tqdm import tqdm

from .utils import MovingAvg


class ModelBase():

	def __init__(self, name, loader, log_fname = ''):
		self._name = name
		self._model = None
		self._loader = loader

		self._epoch = 1
		self._metrics = []

		# Set default log file name if none provided
		if len(log_fname) == 0:
			self._log_fname = '%s.log' % name
		else:
			self._log_fname = log_fname


	def create(self):
		# Override this
		pass


	def compile(self):
		# Override this
		pass


	# Load model for certain epoch
	def load(self, epoch_num, data_dir = 'weights'):
		if not os.path.exists(data_dir):
			os.mkdir(data_dir)

		fname = os.path.join(data_dir, '%s_%d.hdf5' % (self._name, epoch_num))

		if (os.path.exists(fname)):
			self._model.load_weights(fname)
			self._epoch = epoch_num
		else:
			print('Model file', fname, 'does not exist')

		self._epoch = epoch_num + 1


	def train(self, num_epochs, mb_size, test_freq, save_dir = 'weights'):
		start = self._epoch

		# Calculate minibatches per epoch
		mb_per_epoch = self._loader.get_epoch_size() // mb_size

		# Setup log file
		if os.path.exists(self._log_fname):
			if self._epoch == 1:
				os.remove(self._log_fname)
				with open(self._log_fname, 'w'):
					pass

			with open(self._log_fname, 'r') as f:
				log_file = f.read()
		else:
			log_file = ''


		# Start epochs
		for epoch in range(start, num_epochs + 1):
			self._epoch = epoch
			print('Epoch', epoch)

			# Average values
			avgs = []
			for i in range(len(self._metrics)):
				avgs.append(MovingAvg(100))
			total_avgs = [0.0] * len(self._metrics)
			testing_avgs = [0.0] * len(self._metrics)
			num_tests = 0

			progress = tqdm(range(mb_per_epoch))

			# Train all minibatches in epoch
			for mb in progress:
				# Train
				batch = self._loader.get_training_batch(mb_size)
				metrics = self._train_mb(batch)

				# Do testing if needed
				if mb % test_freq == 0:
					batch = self._loader.get_testing_batch(mb_size)
					test_metrics = self._test_mb(batch)
					num_tests += 1

					# Update test metrics
					for i in range(len(self._metrics)):
						testing_avgs[i] += test_metrics[i]

				# Update metrics
				prog_label = ''
				for i in range(len(self._metrics)):
					avgs[i].add(metrics[i])
					total_avgs[i] += metrics[i]

					prog_label += '%s: %.3f | ' % (self._metrics[i], avgs[i].value())

				progress.set_description(prog_label)


			# Print testing metrics
			if len(testing_avgs) > 0:
				print('Testing metrics:')
				for i in range(len(self._metrics)):
					print('%s: %.3f' % (self._metrics[i], testing_avgs[i] / num_tests))
				print('')

			# Save weights
			if not os.path.exists(save_dir):
				os.mkdir(save_dir)
			fname = os.path.join(save_dir, '%s_%d.hdf5' % (self._name, epoch))
			self._model.save_weights(fname)

			# Write log file
			log_file += '\nEpoch %d\n' % epoch
			for i in range(len(metrics)):
				log_file += 'Train %s: %.3f\n' % (self._metrics[i], total_avgs[i] / mb_per_epoch)
				log_file += 'Test  %s: %.3f\n' % (self._metrics[i], testing_avgs[i] / num_tests)
				
			with open(self._log_fname, 'w+') as f:
				f.write(log_file)


	# Given batch data, run one iteration of training
	def _train_mb(self, batch):
		# Default implementation of train minibatch

		# This assumes that batch[0] are the features and batch[1] are the labels

		return self._model.train_on_batch(batch[0], batch[1])


	def _test_mb(self, batch):
		# Default implementation of test minibatch

		# This assumes that batch[0] are the features and batch[1] are the labels

		return self._model.test_on_batch(batch[0], batch[1])