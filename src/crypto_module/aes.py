from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import numpy as np
import hashlib

class AES:
    def __init__(self, password, salt, key_len=256):
        self.block_size = 16
        self.salt = salt
        self.key_len = key_len
        self.password = password.encode("UTF-8")
        self.key, self.hmac_key = self.KeyGeneration(self.password, self.salt)
        
        self.rounds = self.key_len // 32 + 6
        
        self.S_box = np.array(
            [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
            0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
            0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
            0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
            0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
            0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
            0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
            0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
            0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
            0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
            0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
            0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
            0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
            0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
            0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
            0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16], np.uint8)
    
        self.keys = self.KeyExpansion(key=self.key, rounds=self.rounds)
        
    def KeyGeneration(self, password, salt):
        n_bytes = self.key_len // 8
        
        key_bytes = hashlib.scrypt(
            password, salt=salt, n=2**15, r=8, p=1, maxmem=2**26, dklen=n_bytes*2
        )
        
        encryption_key = key_bytes[:n_bytes]
        hmac_key = key_bytes[n_bytes:]
        
        key = np.frombuffer(encryption_key, dtype=np.uint8).reshape((n_bytes // 4, 4))
        return (key, hmac_key)
    
    def KeyExpansion(self, key, rounds):
        rcon = [np.zeros(4, dtype="uint8") for _ in range(11)]
        rcon[1][0] = 1
        for i in range(2, 11):
            rcon[i][0] = (rcon[i - 1][0] << 1) ^ (0x11B & -(rcon[i - 1][0] >> 7))
            
        N = self.key_len // 32
        R = rounds + 1
        
        keys = np.asarray([np.zeros(4, dtype="uint8") for _ in range(4 * R)])
        
        for i in range(4 * R):
            if i < N:
                keys[i] = key[i]
            elif i % N == 0:
                keys[i] = (
                    keys[i - N] ^ self.S_box[np.roll(keys[i - 1], -1)] ^ rcon[i // N]
                )
            elif (N > 6) and (i % N == 4):
                keys[i] = keys[i - N] ^ self.S_box[keys[i - 1]]
            else:
                keys[i] = keys[i - N] ^ keys[i - 1]
                
        keys = np.split(keys, R)
        
        keys = [np.transpose(i) for i in keys]
        return keys
    
    def AddRoundKey(self, state, key):
        return np.bitwise_xor(state, key)
    
    def SubBytes(self, state):
        return self.S_box[state]
    
    def ShiftRows(self, state):
        return np.array([
            state[0],
            np.roll(state[1], -1),
            np.roll(state[2], -2),
            np.roll(state[3], -3)
        ])
        # return state.flatten().take(0, 1, 2, 3, 5, 6, 7, 4, 10, 11, 8, 9, 15, 12, 13, 14).reshape(4, 4)
    
    def MixColumns(self, state):
        def single_col(col):
            b = (col << 1) ^ (0x11B & -(col >> 7))
            
            col_mixed = [
                b[0] ^ col[3] ^ col[2] ^ b[1] ^ col[1],
                b[1] ^ col[0] ^ col[3] ^ b[2] ^ col[2],
                b[2] ^ col[1] ^ col[0] ^ b[3] ^ col[3],
                b[3] ^ col[2] ^ col[1] ^ b[0] ^ col[0],
            ]
            return col_mixed
        
        state[:, 0] = single_col(state[:, 0])
        state[:, 1] = single_col(state[:, 1])
        state[:, 2] = single_col(state[:, 2])
        state[:, 3] = single_col(state[:, 3])
        return state
    
    def encrypt(self, plaintext):
        assert len(plaintext) == self.block_size, "Plaintext must be 128 bits."

        # Create the state
        state = (
            np.frombuffer(plaintext, dtype=np.uint8).reshape((4, 4), order="F").copy()
        )

        # AddRoundKey for initial round
        state = self.AddRoundKey(state=state, key=self.keys[0])

        for i in range(1, self.rounds):
            state = self.SubBytes(state=state)
            state = self.ShiftRows(state=state)
            state = self.MixColumns(state=state)
            state = self.AddRoundKey(state=state, key=self.keys[i])

        # Final round (doesn't MixColumns)
        state = self.SubBytes(state=state)
        state = self.ShiftRows(state=state)
        state = self.AddRoundKey(state=state, key=self.keys[self.rounds])

        ciphertext = state.flatten(order="F")

        return ciphertext
    
    def InvSubBytes(self, state):
        inv_S_box = np.argsort(self.S_box)
        return inv_S_box[state]

    def InvShiftRows(self, state):
        return np.array([
            state[0],
            np.roll(state[1], 1),
            np.roll(state[2], 2),
            np.roll(state[3], 3)
        ])
        
    def InvMixColumns(self, state):
        def single_col(col):
            # Tương tự như MixColumns, nhưng với ma trận nghịch đảo
            a = col.copy()
            b = (a << 1) ^ (0x11B & -(a >> 7))
            c = (b << 1) ^ (0x11B & -(b >> 7))
            d = (c << 1) ^ (0x11B & -(c >> 7))
            
            col_mixed = [
                d[0] ^ c[0] ^ b[0] ^ d[1] ^ b[1] ^ a[1] ^ d[2] ^ c[2] ^ a[2] ^ d[3] ^ a[3],
                d[1] ^ c[1] ^ b[1] ^ d[2] ^ b[2] ^ a[2] ^ d[3] ^ c[3] ^ a[3] ^ d[0] ^ a[0],
                d[2] ^ c[2] ^ b[2] ^ d[3] ^ b[3] ^ a[3] ^ d[0] ^ c[0] ^ a[0] ^ d[1] ^ a[1],
                d[3] ^ c[3] ^ b[3] ^ d[0] ^ b[0] ^ a[0] ^ d[1] ^ c[1] ^ a[1] ^ d[2] ^ a[2]
            ]
            return col_mixed

        state[:, 0] = single_col(state[:, 0])
        state[:, 1] = single_col(state[:, 1])
        state[:, 2] = single_col(state[:, 2])
        state[:, 3] = single_col(state[:, 3])
        return state
    
    def decrypt(self, ciphertext):
        assert len(ciphertext) == self.block_size, "Ciphertext must be 128 bits."

        # Tạo state từ ciphertext
        state = np.frombuffer(ciphertext, dtype=np.uint8).reshape((4, 4), order="F").copy()

        # AddRoundKey cho vòng cuối cùng
        state = self.AddRoundKey(state=state, key=self.keys[self.rounds])

        for i in range(self.rounds-1, 0, -1):
            state = self.InvShiftRows(state=state)
            state = self.InvSubBytes(state=state)
            state = self.AddRoundKey(state=state, key=self.keys[i])
            state = self.InvMixColumns(state=state)

        # Vòng cuối (không có InvMixColumns)
        state = self.InvShiftRows(state=state)
        state = self.InvSubBytes(state=state)
        state = self.AddRoundKey(state=state, key=self.keys[0])

        plaintext = state.flatten(order="F")

        return plaintext
    
