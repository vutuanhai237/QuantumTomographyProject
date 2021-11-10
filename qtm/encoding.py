"""
Function to load classical data in a quantum device
This code is copy from https://github.com/adjs/dcsp/blob/master/encoding.py
"""

import numpy as np
import qiskit

class bin_tree:
    size = None
    values = None

    def __init__(self, values):
        self.size = len(values)
        self.values = values

    def parent(self, key):
        return int((key-0.5)/2)

    def left(self, key):
        return int(2 * key + 1)

    def right(self, key):
        return int(2 * key + 2)

    def root(self):
        return 0

    def __getitem__(self, key):
        return self.values[key]


class Encoding:
    qcircuit = None
    quantum_data = None
    classical_data = None
    num_qubits = None
    tree = None
    output_qubits = []

    def __init__(self, input_vector, encode_type='amplitude_encoding'):
        if encode_type == 'amplitude_encoding':
            self.amplitude_encoding(input_vector)
        if encode_type == 'qubit_encoding':
            self.qubit_encoding(input_vector)
        if encode_type == 'dc_amplitude_encoding':
            self.dc_amplitude_encoding(input_vector)
        if encode_type == 'basis_encoding':
            self.basis_encoding(input_vector)

    def basis_encoding(self, input_vector, n_classical=1):
        """
        encoding a binary string x in a basis state |x>
        """
        self.num_qubits = int(len(input_vector))
        self.quantum_data = qiskit.QuantumRegister(self.num_qubits)
        self.classical_data = qiskit.ClassicalRegister(n_classical)
        self.qcircuit = qiskit.QuantumCircuit(self.quantum_data, self.classical_data)
        for k, _ in enumerate(input_vector):
            if input_vector[k] == 1:
                self.qcircuit.x(self.quantum_data[k])


    def qubit_encoding(self, input_vector, n_classical=1):
        """
        encoding a binary string x as
        """
        input_pattern = qiskit.QuantumRegister(len(input_vector))
        classical_register = qiskit.ClassicalRegister(n_classical)
        self.qcircuit = qiskit.QuantumCircuit(input_pattern, classical_register)
        for k, _ in enumerate(input_vector):
            self.qcircuit.ry(input_vector[k], input_pattern[k])

    @staticmethod
    def _recursive_compute_beta(input_vector, betas):
        if len(input_vector) > 1:
            new_x = []
            beta = []
            for k in range(0, len(input_vector), 2):
                norm = np.sqrt(input_vector[k] ** 2 + input_vector[k + 1] ** 2)
                new_x.append(norm)
                if norm == 0:
                    beta.append(0)
                else:
                    if input_vector[k] < 0:
                        beta.append(2 * np.pi - 2 * np.arcsin(input_vector[k + 1] / norm)) ## testing
                    else:
                        beta.append(2 * np.arcsin(input_vector[k + 1] / norm))
            Encoding._recursive_compute_beta(new_x, betas)
            betas.append(beta)
            output = []

    @staticmethod
    def _index(k, circuit, control_qubits, numberof_controls):
        binary_index = '{:0{}b}'.format(k, numberof_controls)
        for j, qbit in enumerate(control_qubits):
            if binary_index[j] == '1':
                circuit.x(qbit)


    def amplitude_encoding(self, input_vector):
        """
        load real vector x to the amplitude of a quantum state
        """
        self.num_qubits = int(np.log2(len(input_vector)))
        self.quantum_data = qiskit.QuantumRegister(self.num_qubits)
        self.qcircuit = qiskit.QuantumCircuit(self.quantum_data)
        newx = np.copy(input_vector)
        betas = []
        Encoding._recursive_compute_beta(newx, betas)
        self._generate_circuit(betas, self.qcircuit, self.quantum_data)

    def dc_amplitude_encoding(self, input_vector):
        self.num_qubits = int(len(input_vector))-1
        self.quantum_data = qiskit.QuantumRegister(self.num_qubits)
        self.qcircuit = qiskit.QuantumCircuit(self.quantum_data)
        newx = np.copy(input_vector)
        betas = []
        Encoding._recursive_compute_beta(newx, betas)
        self._dc_generate_circuit(betas, self.qcircuit, self.quantum_data)

    def _dc_generate_circuit(self, betas, qcircuit, quantum_input):

        k = 0
        linear_angles = []
        for angles in betas:
            linear_angles = linear_angles + angles
            for angle in angles:
                qcircuit.ry(angle, quantum_input[k])
                k += 1

        self.tree = bin_tree(quantum_input)
        my_tree = self.tree

        last = my_tree.size - 1
        actual = my_tree.parent(last)
        level = my_tree.parent(last)
        while actual >= 0:
            left_index = my_tree.left(actual)
            right_index = my_tree.right(actual)
            while right_index <= last:

                qcircuit.cswap(my_tree[actual], my_tree[left_index], my_tree[right_index])

                left_index = my_tree.left(left_index)
                right_index = my_tree.left(right_index)
            actual -= 1
            if level != my_tree.parent(actual):
                level -= 1

        # set output qubits
        next_index = 0
        while next_index < my_tree.size:
            self.output_qubits.append(next_index)
            next_index = my_tree.left(next_index)

    def _generate_circuit(self, betas, qcircuit, quantum_input):
        numberof_controls = 0  # number of controls
        control_bits = []
        for angles in betas:
            if numberof_controls == 0:
                qcircuit.ry(angles[0], quantum_input[self.num_qubits-1])
                numberof_controls += 1
                control_bits.append(quantum_input[self.num_qubits-1])
            else:
                for k, angle in enumerate(reversed(angles)):
                    Encoding._index(k, qcircuit, control_bits, numberof_controls)

                    qcircuit.mcry(angle,
                                  control_bits,
                                  quantum_input[self.num_qubits - 1 - numberof_controls],
                                  None,
                                  mode='noancilla')

                    Encoding._index(k, qcircuit, control_bits, numberof_controls)
                control_bits.append(quantum_input[self.num_qubits - 1 - numberof_controls])
                numberof_controls += 1